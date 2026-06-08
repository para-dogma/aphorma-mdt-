"""JWT Token Manager with refresh and revocation"""
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import redis
import os

class TokenManager:
    def __init__(self, secret_key: str = None, redis_url: str = None):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'dev-secret-change-in-production')
        self.algorithm = 'HS256'
        self.access_token_expiry = timedelta(minutes=15)
        self.refresh_token_expiry = timedelta(days=7)
        
        # Redis для blacklist и refresh tokens
        self.redis = redis.Redis.from_url(
            redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
    
    def generate_token_pair(self, user_id: str, role: str = 'user') -> Dict[str, str]:
        """Generate access + refresh token pair"""
        now = datetime.utcnow()
        
        # Access token (короткоживущий)
        access_payload = {
            'user_id': user_id,
            'role': role,
            'type': 'access',
            'iat': now,
            'exp': now + self.access_token_expiry,
            'jti': hashlib.sha256(f'{user_id}{now}'.encode()).hexdigest()
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        # Refresh token (долгоживущий)
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': now,
            'exp': now + self.refresh_token_expiry,
            'jti': hashlib.sha256(f'{user_id}{now}refresh'.encode()).hexdigest()
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Сохраняем refresh token в Redis
        self.redis.setex(            f'refresh_token:{refresh_payload["jti"]}',
            int(self.refresh_token_expiry.total_seconds()),
            user_id
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(self.access_token_expiry.total_seconds())
        }
    
    def verify_access_token(self, token: str) -> Optional[Dict]:
        """Verify access token and check blacklist"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Проверяем blacklist
            jti = payload.get('jti')
            if jti and self.redis.exists(f'blacklist:{jti}'):
                return None
            
            # Проверяем тип
            if payload.get('type') != 'access':
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get('type') != 'refresh':
                return None
            
            jti = payload.get('jti')
            
            # Проверяем что refresh token валиден в Redis
            user_id = self.redis.get(f'refresh_token:{jti}')
            if not user_id:
                return None
            
            # Аннулируем старый refresh token (rotation)
            self.redis.delete(f'refresh_token:{jti}')
            
            # Генерируем новую пару            return self.generate_token_pair(user_id, payload.get('role', 'user'))
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke token (add to blacklist)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload.get('jti')
            exp = payload.get('exp')
            
            if jti and exp:
                # Добавляем в blacklist на время оставшейся жизни токена
                ttl = max(0, exp - int(datetime.utcnow().timestamp()))
                self.redis.setex(f'blacklist:{jti}', ttl, 'revoked')
                return True
            return False
        except jwt.InvalidTokenError:
            return False
    
    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for user"""
        # Находим все refresh tokens пользователя
        pattern = f'refresh_token:*'
        for key in self.redis.scan_iter(match=pattern):
            if self.redis.get(key) == user_id:
                jti = key.split(':')[1]
                self.redis.delete(key)
                self.redis.setex(f'blacklist:{jti}', 86400, 'revoked')

token_manager = TokenManager()
