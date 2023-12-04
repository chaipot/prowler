from re import search
from unittest import mock

from boto3 import client
from moto import mock_s3

from tests.providers.aws.audit_info_utils import (
    AWS_ACCOUNT_NUMBER,
    AWS_REGION_EU_WEST_1,
    set_mocked_aws_audit_info,
)

AWS_ACCOUNT_ARN = f"arn:aws:iam::{AWS_ACCOUNT_NUMBER}:root"


class Test_s3_bucket_no_mfa_delete:
    @mock_s3
    def test_no_buckets(self):
        from prowler.providers.aws.services.s3.s3_service import S3

        audit_info = set_mocked_aws_audit_info([AWS_REGION_EU_WEST_1])

        with mock.patch(
            "prowler.providers.aws.lib.audit_info.audit_info.current_audit_info",
            new=audit_info,
        ):
            with mock.patch(
                "prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete.s3_client",
                new=S3(audit_info),
            ):
                # Test Check
                from prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete import (
                    s3_bucket_no_mfa_delete,
                )

                check = s3_bucket_no_mfa_delete()
                result = check.execute()

                assert len(result) == 0

    @mock_s3
    def test_bucket_without_mfa(self):
        s3_client_us_east_1 = client("s3", region_name="us-east-1")
        bucket_name_us = "bucket_test_us"
        s3_client_us_east_1.create_bucket(Bucket=bucket_name_us)

        from prowler.providers.aws.services.s3.s3_service import S3

        audit_info = set_mocked_aws_audit_info([AWS_REGION_EU_WEST_1])

        with mock.patch(
            "prowler.providers.aws.lib.audit_info.audit_info.current_audit_info",
            new=audit_info,
        ):
            with mock.patch(
                "prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete.s3_client",
                new=S3(audit_info),
            ):
                # Test Check
                from prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete import (
                    s3_bucket_no_mfa_delete,
                )

                check = s3_bucket_no_mfa_delete()
                result = check.execute()

                assert len(result) == 1
                assert result[0].status == "FAIL"
                assert search(
                    "MFA Delete disabled",
                    result[0].status_extended,
                )
                assert result[0].resource_id == bucket_name_us
                assert (
                    result[0].resource_arn
                    == f"arn:{audit_info.audited_partition}:s3:::{bucket_name_us}"
                )

    @mock_s3
    def test_bucket_with_mfa(self):
        s3_client_us_east_1 = client("s3", region_name="us-east-1")
        bucket_name_us = "bucket_test_us"
        s3_client_us_east_1.create_bucket(Bucket=bucket_name_us)
        s3_client_us_east_1.put_bucket_versioning(
            Bucket=bucket_name_us,
            VersioningConfiguration={"MFADelete": "Enabled", "Status": "Enabled"},
        )

        from prowler.providers.aws.services.s3.s3_service import S3

        audit_info = set_mocked_aws_audit_info([AWS_REGION_EU_WEST_1])
        with mock.patch(
            "prowler.providers.aws.lib.audit_info.audit_info.current_audit_info",
            new=audit_info,
        ):
            with mock.patch(
                "prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete.s3_client",
                new=S3(audit_info),
            ) as service_client:
                # Test Check
                from prowler.providers.aws.services.s3.s3_bucket_no_mfa_delete.s3_bucket_no_mfa_delete import (
                    s3_bucket_no_mfa_delete,
                )

                service_client.buckets[0].mfa_delete = True
                check = s3_bucket_no_mfa_delete()
                result = check.execute()

                assert len(result) == 1
                assert result[0].status == "PASS"
                assert search(
                    "MFA Delete enabled",
                    result[0].status_extended,
                )
                assert result[0].resource_id == bucket_name_us
                assert (
                    result[0].resource_arn
                    == f"arn:{audit_info.audited_partition}:s3:::{bucket_name_us}"
                )
