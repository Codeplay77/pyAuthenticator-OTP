"""
Database Management Module for Python Authenticator

This module handles all database operations including:
- Account storage and retrieval
- Secret key encryption/decryption
- Database schema management
- Secure key file management

Security:
    All TOTP secret keys are encrypted using Fernet (symmetric encryption)
    before being stored in the database. The encryption key is stored
    separately in a key.key file.

Author: Codeplay
Date: June 2025
"""

import os
import sys
import base64
import sqlite3
from typing import List, Tuple

from cryptography.fernet import Fernet


class Database:
    """
    Database manager for TOTP account storage.
    
    Provides a secure interface for storing and retrieving 2FA accounts
    with encrypted secret keys. Uses SQLite for storage and Fernet for
    symmetric encryption of sensitive data.
    
    Database Schema:
        accounts table:
            - id: INTEGER PRIMARY KEY AUTOINCREMENT
            - name: TEXT NOT NULL (account name)
            - secret: TEXT NOT NULL (encrypted TOTP secret)
            - issuer: TEXT DEFAULT '' (service provider name)
            - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    Attributes:
        app_dir (str): Application directory path
        db_path (str): Full path to SQLite database file
        key_path (str): Full path to encryption key file
        key (bytes): Fernet encryption key
        cipher (Fernet): Fernet cipher instance
    
    Security Considerations:
        - Secrets are encrypted at rest
        - Key file should be protected with appropriate file permissions
        - Consider key rotation strategy for production environments
        - Database file should be backed up securely
    """
    
    def __init__(self) -> None:
        """
        Initialize database connection and encryption.
        
        Determines the appropriate directory for database files based on
        whether the application is running as a frozen executable or script.
        Creates encryption key if it doesn't exist.
        
        Raises:
            Exception: If encryption setup or database creation fails
        """
        self.app_dir = self.get_app_directory()
        self.db_path = os.path.join(self.app_dir, "authenticator.db")
        self.key_path = os.path.join(self.app_dir, "key.key")

        self.setup_encryption()
        self.setup_database()
    
    def get_app_directory(self) -> str:
        """Determine the appropriate application directory.
        
        Returns different paths based on execution context:
        - Frozen executable (PyInstaller): Directory containing .exe
        - Python script: Directory containing the script file
        
        This ensures data files are stored in predictable locations
        regardless of how the application is run.
        
        Returns:
            str: Absolute path to application directory
            
        Note:
            PyInstaller sets sys.frozen attribute when creating executables.
        """
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))
    
    def setup_encryption(self) -> None:
        """Configure Fernet symmetric encryption for secret keys.
        
        Generates a new encryption key if one doesn't exist, or loads
        the existing key. The key is used to encrypt/decrypt TOTP secrets
        before storage in the database.
        
        Encryption Flow:
            1. Check if key.key file exists
            2. If not, generate new Fernet key and save to file
            3. Load key from file
            4. Initialize Fernet cipher instance
        
        Raises:
            Exception: If key file cannot be created or read
            
        Security Note:
            The encryption key file should be protected with appropriate
            file system permissions. Consider using OS keyring in production.
        """
        try:
            if not os.path.exists(self.key_path):
                print(f"Criando nova chave de criptografia em: {self.key_path}")
                key = Fernet.generate_key()
                with open(self.key_path, 'wb') as key_file:
                    key_file.write(key)
            else:
                print(f"Carregando chave existente de: {self.key_path}")
            
            with open(self.key_path, 'rb') as key_file:
                self.key = key_file.read()
            
            self.cipher = Fernet(self.key)
            print("Criptografia configurada com sucesso")
            
        except Exception as e:
            print(f"Erro ao configurar criptografia: {e}")
            raise
    
    def setup_database(self) -> None:
        """Initialize SQLite database and create schema.
        
        Creates the accounts table if it doesn't exist. Uses CREATE TABLE
        IF NOT EXISTS to ensure idempotency (safe to call multiple times).
        
        Table Schema:
            - id: Auto-incrementing primary key
            - name: Account name (e.g., "john@example.com")
            - secret: Encrypted TOTP secret key
            - issuer: Service provider (e.g., "Google", "GitHub")
            - created_at: Timestamp of account creation
        
        Raises:
            sqlite3.Error: If database creation or table creation fails
        """
        try:
            print(f"Configurando banco de dados em: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    issuer TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("Banco de dados configurado com sucesso")
            
        except Exception as e:
            print(f"Erro ao configurar banco: {e}")
            raise
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a TOTP secret key for storage.
        
        Args:
            secret: Plain text TOTP secret key (Base32 encoded)
            
        Returns:
            Base64 encoded encrypted secret
            
        Process:
            1. Encode secret as UTF-8 bytes
            2. Encrypt using Fernet cipher
            3. Base64 encode the encrypted bytes
            4. Decode to string for database storage
        """
        return base64.b64encode(self.cipher.encrypt(secret.encode())).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt an encrypted TOTP secret key.
        
        Args:
            encrypted_secret: Base64 encoded encrypted secret from database
            
        Returns:
            Plain text TOTP secret key
            
        Process:
            1. Decode Base64 string to bytes
            2. Decrypt using Fernet cipher
            3. Decode UTF-8 bytes to string
            
        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        return self.cipher.decrypt(base64.b64decode(encrypted_secret.encode())).decode()
    
    def add_account(self, name: str, secret: str, issuer: str = "") -> int:
        """Add a new 2FA account to the database.
        
        Args:
            name: Account identifier (email, username, etc.)
            secret: Plain text TOTP secret key (will be encrypted)
            issuer: Service provider name (optional)
            
        Returns:
            int: Database ID of the newly created account
            
        Raises:
            sqlite3.Error: If database insert fails
            Exception: If encryption fails
            
        Note:
            The secret is automatically encrypted before storage.
            Duplicate accounts are allowed (no unique constraint).
        """
        try:
            print(f"Adicionando conta: {name}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            encrypted_secret = self.encrypt_secret(secret)
            
            cursor.execute("""
                INSERT INTO accounts (name, secret, issuer)
                VALUES (?, ?, ?)
            """, (name, encrypted_secret, issuer))
            
            account_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"Conta adicionada com ID: {account_id}")
            return account_id
            
        except Exception as e:
            print(f"Erro ao adicionar conta: {e}")
            raise
    
    def get_all_accounts(self) -> List[Tuple[int, str, str, str]]:
        """Retrieve all accounts from the database.
        
        Returns:
            List of tuples, each containing:
                - id (int): Account database ID
                - name (str): Account name
                - secret (str): Decrypted TOTP secret
                - issuer (str): Service provider name
            
            Returns empty list if database doesn't exist or on error.
            
        Note:
            Secrets are automatically decrypted before returning.
            Accounts with decryption errors are skipped with a warning log.
            Results are sorted alphabetically by account name.
        """
        try:
            if not os.path.exists(self.db_path):
                print("Banco de dados não existe ainda")
                return []
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, secret, issuer FROM accounts ORDER BY name")
            accounts = cursor.fetchall()
            
            conn.close()

            decrypted_accounts = []
            for account in accounts:
                try:
                    id_, name, encrypted_secret, issuer = account
                    secret = self.decrypt_secret(encrypted_secret)
                    decrypted_accounts.append((id_, name, secret, issuer))
                except Exception as e:
                    print(f"Erro ao descriptografar conta {id_}: {e}")
                    continue
            
            print(f"Carregadas {len(decrypted_accounts)} contas")
            return decrypted_accounts
            
        except Exception as e:
            print(f"Erro ao carregar contas: {e}")
            return []
    
    def delete_account(self, account_id: int) -> None:
        """Delete an account from the database.
        
        Args:
            account_id: Database ID of the account to delete
            
        Raises:
            sqlite3.Error: If database delete operation fails
            
        Note:
            This is a permanent operation with no undo capability.
            Consider implementing soft deletes for production use.
        """
        try:
            print(f"Removendo conta ID: {account_id}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            
            conn.commit()
            conn.close()
            print("Conta removida com sucesso")
            
        except Exception as e:
            print(f"Erro ao remover conta: {e}")
            raise
    
    def update_account(self, account_id, name, secret, issuer=""):
        """Atualiza uma conta"""
        try:
            print(f"Atualizando conta ID: {account_id}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            encrypted_secret = self.encrypt_secret(secret)
            
            cursor.execute("""
                UPDATE accounts 
                SET name = ?, secret = ?, issuer = ?
                WHERE id = ?
            """, (name, encrypted_secret, issuer, account_id))
            
            conn.commit()
            conn.close()
            print("Conta atualizada com sucesso")
            
        except Exception as e:
            print(f"Erro ao atualizar conta: {e}")
            raise
    
    def get_database_info(self):
        """Retorna informações sobre o banco para debug"""
        return {
            'app_dir': self.app_dir,
            'db_path': self.db_path,
            'key_path': self.key_path,
            'db_exists': os.path.exists(self.db_path),
            'key_exists': os.path.exists(self.key_path),
            'app_dir_writable': os.access(self.app_dir, os.W_OK),
            'frozen': getattr(sys, 'frozen', False)
        }