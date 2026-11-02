"""
TOTP (Time-based One-Time Password) Generator Module

This module provides TOTP token generation functionality compatible with
Google Authenticator, Microsoft Authenticator, and other RFC 6238 compliant
authentication applications.

Standards:
    - RFC 6238: TOTP specification
    - RFC 4648: Base32 encoding
    
Algorithm:
    TOTP = HOTP(K, T) where:
    - K = shared secret key
    - T = floor((current Unix time) / time step)
    - Time step = 30 seconds (standard)

Author: Codeplay
Date: June 2025
"""

import re
import time
from typing import Tuple, Optional, Dict

import pyotp


class TOTPGenerator:
    """Generate and validate TOTP tokens.
    
    This class implements Time-based One-Time Password (TOTP) generation
    according to RFC 6238. Tokens are generated using HMAC-SHA1 and are
    valid for a 30-second time window.
    
    Attributes:
        period (int): Time step in seconds (default: 30)
        
    Compatibility:
        Generated tokens are compatible with:
        - Google Authenticator
        - Microsoft Authenticator
        - Authy
        - Any RFC 6238 compliant authenticator
    """
    
    def __init__(self) -> None:
        """Initialize TOTP generator with standard 30-second period."""
        self.period = 30

    def clean_secret(self, secret: str) -> str:
        """Normalize a TOTP secret key.

        Removes whitespace, dashes and Base32 padding ("=") and converts
        to uppercase. Any other character is kept so validate_secret()
        can reject it instead of silently changing the key.

        Args:
            secret: Raw secret key (may contain spaces, dashes, etc.)

        Returns:
            Normalized secret

        Examples:
            >>> clean_secret("JBSW Y3DP EHPK 3PXP")
            'JBSWY3DPEHPK3PXP'
            >>> clean_secret("jbsw-y3dp-ehpk-3pxp")
            'JBSWY3DPEHPK3PXP'
        """
        return re.sub(r'[\s=-]', '', secret).upper()

    def validate_secret(self, secret: str) -> Tuple[bool, str]:
        """Validate TOTP secret key format and length.

        Performs comprehensive validation:
        1. Cleans the secret key
        2. Checks minimum length (8 characters)
        3. Validates Base32 alphabet
        4. Generates a token to confirm the key decodes as Base32
        
        Args:
            secret: Secret key to validate
            
        Returns:
            Tuple of (is_valid, message):
                - is_valid: True if secret is valid
                - message: Success message or error description
                
        Examples:
            >>> validate_secret("JBSWY3DPEHPK3PXP")
            (True, "Chave válida")
            >>> validate_secret("ABC")
            (False, "Chave muito curta (mínimo 8 caracteres)")
        """
        cleaned_secret = self.clean_secret(secret)
        
        if len(cleaned_secret) < 8:
            return False, "Chave muito curta (mínimo 8 caracteres)"
        
        if not re.match(r'^[A-Z2-7]+$', cleaned_secret):
            return False, "Chave contém caracteres inválidos"
        
        try:
            pyotp.TOTP(cleaned_secret).now()
        except Exception:
            return False, "Tamanho de chave inválido para Base32"
        return True, "Chave válida"
    
    def generate_token(self, secret: str) -> str:
        """Generate current TOTP token.
        
        Generates a 6-digit one-time password based on the current time
        and the provided secret key. The token changes every 30 seconds.
        
        Args:
            secret: TOTP secret key (Base32 encoded)
            
        Returns:
            6-digit token as string (e.g., "123456")
            Returns "ERROR" if generation fails
            
        Algorithm:
            1. Clean and normalize the secret
            2. Calculate time step (Unix time / 30)
            3. Generate HMAC-SHA1 hash
            4. Apply dynamic truncation
            5. Return 6-digit code
            
        Note:
            Token is zero-padded to ensure 6 digits (e.g., "000123").
        """
        try:
            cleaned_secret = self.clean_secret(secret)
            totp = pyotp.TOTP(cleaned_secret)
            token = totp.now()
            return f"{int(token):06d}"
        except Exception:
            return "ERROR"
    
    def get_time_remaining(self) -> int:
        """Calculate seconds remaining until next token.
        
        Returns:
            int: Seconds remaining in current 30-second period (1-30)
            
        Example:
            If current time is 12:00:25, returns 5 seconds.
            If current time is 12:00:00, returns 30 seconds.
        """
        return self.period - (int(time.time()) % self.period)
    
    def get_progress_percentage(self) -> float:
        """Calculate token expiration progress.
        
        Returns:
            float: Progress percentage (0.0 to 100.0)
            
        Usage:
            Useful for displaying progress bars or visual indicators
            of token validity lifetime.
            
        Example:
            If 20 seconds elapsed in 30-second period, returns 66.67.
        """
        remaining = self.get_time_remaining()
        return ((self.period - remaining) / self.period) * 100
    
    def parse_otpauth_url(self, url: str) -> Tuple[Optional[Dict[str, str]], str]:
        """Parse an otpauth:// URL and extract account information.
        
        Parses QR code URLs in the format:
        otpauth://totp/AccountName?secret=SECRET&issuer=ISSUER
        
        Args:
            url: Complete otpauth:// URL from QR code
            
        Returns:
            Tuple of (result_dict, message):
                - result_dict: Dict with 'name', 'secret', 'issuer' or None
                - message: Success message or error description
                
        URL Format:
            otpauth://totp/[ISSUER:]ACCOUNT?secret=SECRET&issuer=ISSUER
            
        Examples:
            >>> parse_otpauth_url(
            ...     "otpauth://totp/Google:user@gmail.com?"
            ...     "secret=JBSWY3DPEHPK3PXP&issuer=Google"
            ... )
            ({'name': 'Google:user@gmail.com', 
              'secret': 'JBSWY3DPEHPK3PXP',
              'issuer': 'Google'}, 
             'URL analisada com sucesso')
        """
        try:
            if not url.startswith('otpauth://'):
                return None, "URL deve começar com otpauth://"
            
            if 'otpauth://totp/' in url:
                url = url.replace('otpauth://totp/', '')
            else:
                return None, "URL deve ser do tipo TOTP"
            
            if '?' in url:
                account_part, params_part = url.split('?', 1)
            else:
                return None, "URL malformada"
            
            account_name = account_part
            
            params = {}
            for param in params_part.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
            
            if 'secret' not in params:
                return None, "Chave secreta não encontrada na URL"
            
            result = {
                'name': account_name,
                'secret': params['secret'],
                'issuer': params.get('issuer', '')
            }
            
            return result, "URL analisada com sucesso"
            
        except Exception as e:
            return None, f"Erro ao analisar URL: {str(e)}"