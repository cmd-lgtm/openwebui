from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
import pandas as pd
import os

class IntelligentCausalEngine:
    """
    Selects appropriate causal engine based on data size.
    Uses Pandas for datasets < 100K rows, Spark for larger datasets.
    """
    def __init__(self):
        from backend.core.causal import CausalEngine
        self.pandas_engine = CausalEngine()
        self.spark_engine = None  # Lazy initialization
        self.threshold = 100_000  # Rows threshold for engine selection

    async def analyze(self, data_source: str, params: dict = None):
        """
        Determine data size and select appropriate engine.

        Args:
            data_source: "neo4j" or "timescale" - where to fetch data from
            params: Query parameters for data fetching

        Returns:
            Causal analysis results from selected engine
        """
        if params is None:
            params = {}
            
        # Get row count without fetching all data
        row_count = await self._get_row_count(data_source, params)

        if row_count < self.threshold:
            # Use Pandas for small datasets
            df = await self._fetch_pandas(data_source, params)
            return self.pandas_engine.analyze(df)
        else:
            # Use Spark for large datasets
            if not self.spark_engine:
                self.spark_engine = DistributedCausalEngine()

            # Fetch directly into Spark (avoid Pandas conversion)
            spark_df = await self._fetch_spark(data_source, params)
            return self.spark_engine.analyze_spark_df(spark_df)

    async def _get_row_count(self, source: str, params: dict) -> int:
        """
        Get row count without fetching all data.
        Uses COUNT(*) query to avoid loading data into memory.
        """
        if source == "neo4j":
            neo4j_pool = params.get("neo4j_pool")
            if neo4j_pool:
                result = await neo4j_pool.execute_read("MATCH (e:Employee) RETURN count(e) as count", {})
                return result[0]["count"] if result else 0
            else:
                # Fallback to direct connection
                from backend.core.neo4j_adapter import Neo4jAdapter
                adapter = Neo4jAdapter(
                    params.get("neo4j_uri"),
                    params.get("neo4j_user"),
                    params.get("neo4j_password")
                )
                try:
                    with adapter.driver.session() as session:
                        result = session.run("MATCH (e:Employee) RETURN count(e) as count")
                        return result.single()["count"]
                finally:
                    adapter.close()
        else:  # timescale
            timescale_pool = params.get("timescale_pool")
            if timescale_pool:
                query = "SELECT COUNT(*) as count FROM employee_metrics"
                result = await timescale_pool.execute_read(query, [])
                return result[0]["count"] if result else 0
            return 0

    async def _fetch_pandas(self, source: str, params: dict) -> pd.DataFrame:
        """
        Fetch data using Pandas for small datasets.
        """
        if source == "neo4j":
            neo4j_pool = params.get("neo4j_pool")
            if neo4j_pool:
                # Fetch enriched employee data with metrics
                query = """
                MATCH (e:Employee)
                OPTIONAL MATCH (e)-[r:INTERACTS]->()
                WITH e, count(r) as interaction_count
                RETURN 
                    e.id as id,
                    e.name as name,
                    e.team as team,
                    e.role as role,
                    e.is_manager as is_manager,
                    COALESCE(e.degree_centrality, 0.0) as degree_centrality,
                    COALESCE(e.betweenness_centrality, 0.0) as betweenness_centrality,
                    COALESCE(e.clustering_coeff, 0.0) as clustering_coeff,
                    COALESCE(e.burnout_score, 50.0) as burnout_score
                """
                result = await neo4j_pool.execute_read(query, {})
                return pd.DataFrame(result)
            else:
                # Fallback to Neo4jAdapter
                from backend.core.neo4j_adapter import Neo4jAdapter
                adapter = Neo4jAdapter(
                    params.get("neo4j_uri"),
                    params.get("neo4j_user"),
                    params.get("neo4j_password")
                )
                try:
                    return adapter.enrich_and_export()
                finally:
                    adapter.close()
        else:  # timescale
            timescale_pool = params.get("timescale_pool")
            if timescale_pool:
                query = """
                SELECT 
                    employee_id,
                    degree_centrality,
                    betweenness_centrality,
                    clustering_coeff,
                    burnout_score,
                    is_manager
                FROM employee_metrics
                ORDER BY timestamp DESC
                """
                result = await timescale_pool.execute_read(query, [])
                return pd.DataFrame(result)
            return pd.DataFrame()

    async def _fetch_spark(self, source: str, params: dict):
        """
        Fetch data directly into Spark DataFrame for large datasets.
        Avoids Pandas conversion to save memory.
        """
        if not self.spark_engine:
            self.spark_engine = DistributedCausalEngine()

        if source == "neo4j":
            # Use Neo4j Spark connector to read directly
            neo4j_uri = params.get("neo4j_uri", "bolt://localhost:7687")
            neo4j_user = params.get("neo4j_user", "neo4j")
            neo4j_password = params.get("neo4j_password", "causal_organism")

            # Query to fetch enriched employee data with metrics
            query = """
            MATCH (e:Employee)
            OPTIONAL MATCH (e)-[r:INTERACTS]->()
            WITH e, count(r) as interaction_count
            RETURN 
                e.id as id,
                e.name as name,
                e.team as team,
                e.role as role,
                e.is_manager as is_manager,
                COALESCE(e.degree_centrality, 0.0) as degree_centrality,
                COALESCE(e.betweenness_centrality, 0.0) as betweenness_centrality,
                COALESCE(e.clustering_coeff, 0.0) as clustering_coeff,
                COALESCE(e.burnout_score, 50.0) as burnout_score
            """
            
            return self.spark_engine.spark.read.format("org.neo4j.spark.DataSource") \
                .option("url", neo4j_uri) \
                .option("authentication.type", "basic") \
                .option("authentication.basic.username", neo4j_user) \
                .option("authentication.basic.password", neo4j_password) \
                .option("query", query) \
                .load()
        else:  # timescale
            # Use JDBC connector for TimescaleDB
            timescale_host = params.get("timescale_host", "localhost")
            timescale_port = params.get("timescale_port", 5432)
            timescale_database = params.get("timescale_database", "postgres")
            timescale_user = params.get("timescale_user", "postgres")
            timescale_password = params.get("timescale_password", "password")
            
            jdbc_url = f"jdbc:postgresql://{timescale_host}:{timescale_port}/{timescale_database}"
            
            # Query to fetch latest metrics per employee
            query = """
            (SELECT DISTINCT ON (employee_id)
                employee_id,
                degree_centrality,
                betweenness_centrality,
                clustering_coeff,
                burnout_score,
                CAST(is_manager AS INTEGER) as is_manager
            FROM employee_metrics
            ORDER BY employee_id, timestamp DESC) as employee_metrics
            """
            
            return self.spark_engine.spark.read \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", query) \
                .option("user", timescale_user) \
                .option("password", timescale_password) \
                .option("driver", "org.postgresql.Driver") \
                .load()


class DistributedCausalEngine:
    """
    Handles Causal Inference on "Big Data" using Apache Spark.
    """
    def __init__(self):
        # Initialize Spark Session (Local Mode for POC)
        # In production this would connect to a cluster
        self.spark = SparkSession.builder \
            .appName("CausalOrganismDistributed") \
            .config("spark.driver.memory", "2g") \
            .config("spark.jars.packages", "org.neo4j:neo4j-connector-apache-spark_2.12:5.0.0_for_spark_3,org.postgresql:postgresql:42.5.0") \
            .getOrCreate()
        # Set log level to reduce noise
        self.spark.sparkContext.setLogLevel("WARN")
    
    def analyze_spark_df(self, spark_df):
        """
        Analyze data directly from Spark DataFrame without Pandas conversion.
        This method reads directly from databases (Neo4j/TimescaleDB) via Spark connectors.
        """
        print("DistributedCausalEngine: Analyzing Spark DataFrame directly (no Pandas conversion)...")
        
        # Prepare Features
        feature_cols = ["degree_centrality", "is_manager"]
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol="features"
        )
        data = assembler.transform(spark_df).select("features", "burnout_score")
        
        # Run Linear Regression
        print("DistributedCausalEngine: Running SparkML Linear Regression...")
        lr = LinearRegression(featuresCol="features", labelCol="burnout_score")
        model = lr.fit(data)
        
        # Extract Results
        coeffs = model.coefficients
        intercept = model.intercept
        summary = model.summary
        
        results = {
            "coefficients": {
                "intercept": float(intercept),
                "degree_centrality": float(coeffs[0]),
                "is_manager": float(coeffs[1])
            },
            "r_squared": float(summary.r2),
            # pValues order matches feature_cols in VectorAssembler
            "p_values": {
                "degree_centrality": float(summary.pValues[0]),
                "is_manager": float(summary.pValues[1])
            },
            "engine": "spark"
        }
        
        return results
            
    def analyze(self, pandas_df: pd.DataFrame):
        """
        Legacy method for backward compatibility.
        Converts Pandas DataFrame to Spark DataFrame.
        Note: For large datasets, use analyze_spark_df() to avoid Pandas conversion.
        """
        print("DistributedCausalEngine: Converting Pandas DF to Spark DataFrame...")
        
        # Convert Pandas to Spark
        # Note: In a true big data pipeline, we would read directly from source (Neo4j/Parquet)
        # instead of passing through Pandas memory.
        sdf = self.spark.createDataFrame(pandas_df)
        
        # Use the direct Spark DataFrame analysis method
        return self.analyze_spark_df(sdf)

    def stop(self):
        self.spark.stop()
