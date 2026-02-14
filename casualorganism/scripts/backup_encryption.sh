#!/bin/bash
# Backup Encryption Utility
# Provides AES-256 encryption/decryption for backup files

set -e

# Configuration
ACTION="${1:-encrypt}"  # encrypt or decrypt
INPUT_FILE="${2:-}"
OUTPUT_FILE="${3:-}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

# Validate inputs
if [ -z "${INPUT_FILE}" ]; then
    echo "Error: Input file not specified"
    echo "Usage: $0 <encrypt|decrypt> <input_file> [output_file]"
    exit 1
fi

if [ ! -f "${INPUT_FILE}" ]; then
    echo "Error: Input file does not exist: ${INPUT_FILE}"
    exit 1
fi

if [ -z "${ENCRYPTION_KEY}" ]; then
    echo "Error: ENCRYPTION_KEY environment variable not set"
    echo "Set ENCRYPTION_KEY before running this script"
    exit 1
fi

# Set output file if not specified
if [ -z "${OUTPUT_FILE}" ]; then
    if [ "${ACTION}" = "encrypt" ]; then
        OUTPUT_FILE="${INPUT_FILE}.enc"
    elif [ "${ACTION}" = "decrypt" ]; then
        OUTPUT_FILE="${INPUT_FILE%.enc}"
    fi
fi

# Perform action
if [ "${ACTION}" = "encrypt" ]; then
    echo "Encrypting ${INPUT_FILE} with AES-256..."
    
    # Use OpenSSL for AES-256-CBC encryption with PBKDF2 key derivation
    openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
        -in "${INPUT_FILE}" \
        -out "${OUTPUT_FILE}" \
        -k "${ENCRYPTION_KEY}"
    
    if [ $? -eq 0 ]; then
        echo "Encryption successful: ${OUTPUT_FILE}"
        
        # Generate checksum for verification
        CHECKSUM=$(sha256sum "${OUTPUT_FILE}" | awk '{print $1}')
        echo "${CHECKSUM}" > "${OUTPUT_FILE}.sha256"
        echo "Checksum saved: ${OUTPUT_FILE}.sha256"
        
        # Display file sizes
        INPUT_SIZE=$(du -h "${INPUT_FILE}" | awk '{print $1}')
        OUTPUT_SIZE=$(du -h "${OUTPUT_FILE}" | awk '{print $1}')
        echo "Original size: ${INPUT_SIZE}"
        echo "Encrypted size: ${OUTPUT_SIZE}"
    else
        echo "Error: Encryption failed"
        exit 1
    fi
    
elif [ "${ACTION}" = "decrypt" ]; then
    echo "Decrypting ${INPUT_FILE} with AES-256..."
    
    # Verify checksum if available
    if [ -f "${INPUT_FILE}.sha256" ]; then
        echo "Verifying checksum..."
        EXPECTED_CHECKSUM=$(cat "${INPUT_FILE}.sha256")
        ACTUAL_CHECKSUM=$(sha256sum "${INPUT_FILE}" | awk '{print $1}')
        
        if [ "${EXPECTED_CHECKSUM}" != "${ACTUAL_CHECKSUM}" ]; then
            echo "Error: Checksum verification failed!"
            echo "Expected: ${EXPECTED_CHECKSUM}"
            echo "Actual: ${ACTUAL_CHECKSUM}"
            exit 1
        fi
        echo "Checksum verified successfully"
    fi
    
    # Use OpenSSL for AES-256-CBC decryption
    openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
        -in "${INPUT_FILE}" \
        -out "${OUTPUT_FILE}" \
        -k "${ENCRYPTION_KEY}"
    
    if [ $? -eq 0 ]; then
        echo "Decryption successful: ${OUTPUT_FILE}"
        
        # Display file size
        OUTPUT_SIZE=$(du -h "${OUTPUT_FILE}" | awk '{print $1}')
        echo "Decrypted size: ${OUTPUT_SIZE}"
    else
        echo "Error: Decryption failed. Check encryption key."
        exit 1
    fi
    
else
    echo "Error: Invalid action. Use 'encrypt' or 'decrypt'"
    echo "Usage: $0 <encrypt|decrypt> <input_file> [output_file]"
    exit 1
fi

echo "Operation completed successfully!"
