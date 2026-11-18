from datetime import timedelta
import secrets
import unittest
from uuid import uuid4

from src.domain.security.services import HasherService, TokenService
from src.low.exceptions import UnauthorizatedException


class TokenServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TokenService(secrets.token_urlsafe(48), "HS256", 15, 7)
        self.user_id = uuid4()
        self.claims = {"sub": str(self.user_id)}

    def test_access_and_refresh_round_trip(self) -> None:
        access = self.service.create_access_token(self.claims)
        refresh = self.service.create_refresh_token(self.claims)
        self.assertEqual(self.service.get_user_id_from_token(access), self.user_id)
        self.assertEqual(
            self.service.get_user_id_from_refresh_token(refresh), self.user_id
        )
        self.assertEqual(self.claims, {"sub": str(self.user_id)})

    def test_access_and_refresh_are_not_interchangeable(self) -> None:
        with self.assertRaises(UnauthorizatedException):
            self.service.get_user_id_from_token(
                self.service.create_refresh_token(self.claims)
            )
        with self.assertRaises(UnauthorizatedException):
            self.service.get_user_id_from_refresh_token(
                self.service.create_access_token(self.claims)
            )

    def test_expired_tokens_are_rejected(self) -> None:
        for create in (
            self.service.create_access_token,
            self.service.create_refresh_token,
        ):
            with self.subTest(create=create.__name__):
                token = create(self.claims, expires_delta=timedelta(minutes=-1))
                with self.assertRaises(UnauthorizatedException):
                    self.service.decode_token(token)

    def test_invalid_subject_is_rejected(self) -> None:
        for claims in ({}, {"sub": "not-a-uuid"}):
            with self.subTest(claims=claims):
                token = self.service.create_access_token(claims)
                with self.assertRaises(UnauthorizatedException):
                    self.service.get_user_id_from_token(token)

    def test_wrong_signature_and_malformed_tokens_are_rejected(self) -> None:
        other_service = TokenService(secrets.token_urlsafe(48), "HS256", 15, 7)
        for token in ("not-a-jwt", other_service.create_access_token(self.claims)):
            with (
                self.subTest(token=token),
                self.assertRaises(UnauthorizatedException),
            ):
                self.service.decode_token(token)


class PasswordHashTests(unittest.TestCase):
    def test_password_hash_validates_only_matching_password(self) -> None:
        service = HasherService()
        password = secrets.token_urlsafe(12)
        hashed = service.get_password_hash(password)
        self.assertNotEqual(hashed, password)
        self.assertTrue(service.validate_password(password, hashed))
        self.assertFalse(service.validate_password("incorrect", hashed))
