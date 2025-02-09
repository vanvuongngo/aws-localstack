import json

import pytest
from localstack_snapshot.snapshots.transformer import JsonpathTransformer, RegexTransformer

from localstack.testing.pytest import markers
from localstack.testing.pytest.stepfunctions.utils import (
    create_and_record_execution,
    create_state_machine_with_iam_role,
)
from localstack.utils.strings import short_uid
from tests.aws.services.stepfunctions.templates.base.base_templates import BaseTemplate as BT
from tests.aws.services.stepfunctions.templates.services.services_templates import (
    ServicesTemplates as ST,
)


@markers.snapshot.skip_snapshot_verify(
    paths=[
        # TODO: add support for Sdk Http metadata.
        "$..SdkHttpMetadata",
        "$..SdkResponseMetadata",
    ]
)
class TestTaskServiceAwsSdk:
    @markers.snapshot.skip_snapshot_verify(paths=["$..SecretList"])
    @markers.aws.validated
    def test_list_secrets(
        self, aws_client, create_state_machine_iam_role, create_state_machine, sfn_snapshot
    ):
        template = ST.load_sfn_template(ST.AWSSDK_LIST_SECRETS)
        definition = json.dumps(template)
        exec_input = json.dumps(dict())
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    def test_dynamodb_put_get_item(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        dynamodb_create_table,
        snapshot,
    ):
        snapshot.add_transformer(snapshot.transform.dynamodb_api())

        table_name = f"sfn_test_table_{short_uid()}"
        dynamodb_create_table(table_name=table_name, partition_key="id", client=aws_client.dynamodb)

        template = ST.load_sfn_template(ST.AWS_SDK_DYNAMODB_PUT_GET_ITEM)
        definition = json.dumps(template)

        exec_input = json.dumps(
            {
                "TableName": table_name,
                "Item": {"data": {"S": "HelloWorld"}, "id": {"S": "id1"}},
                "Key": {"id": {"S": "id1"}},
            }
        )
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    def test_dynamodb_put_delete_item(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        dynamodb_create_table,
        snapshot,
    ):
        snapshot.add_transformer(snapshot.transform.dynamodb_api())

        table_name = f"sfn_test_table_{short_uid()}"
        dynamodb_create_table(table_name=table_name, partition_key="id", client=aws_client.dynamodb)

        template = ST.load_sfn_template(ST.AWS_SDK_DYNAMODB_PUT_DELETE_ITEM)
        definition = json.dumps(template)

        exec_input = json.dumps(
            {
                "TableName": table_name,
                "Item": {"data": {"S": "HelloWorld"}, "id": {"S": "id1"}},
                "Key": {"id": {"S": "id1"}},
            }
        )
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    def test_dynamodb_put_update_get_item(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        dynamodb_create_table,
        snapshot,
    ):
        snapshot.add_transformer(snapshot.transform.dynamodb_api())

        table_name = f"sfn_test_table_{short_uid()}"
        dynamodb_create_table(table_name=table_name, partition_key="id", client=aws_client.dynamodb)

        template = ST.load_sfn_template(ST.AWS_SDK_DYNAMODB_PUT_UPDATE_GET_ITEM)
        definition = json.dumps(template)

        exec_input = json.dumps(
            {
                "TableName": table_name,
                "Item": {"data": {"S": "HelloWorld"}, "id": {"S": "id1"}},
                "Key": {"id": {"S": "id1"}},
                "UpdateExpression": "set S=:r",
                "ExpressionAttributeValues": {":r": {"S": "HelloWorldUpdated"}},
            }
        )
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            snapshot,
            definition,
            exec_input,
        )

    @markers.snapshot.skip_snapshot_verify(
        paths=[
            # TODO: aws-sdk SFN integration now appears to be inserting decorated error names into the cause messages.
            #  Upcoming work should collect more failure snapshot involving other aws-sdk integrations and trace a
            #  picture of generalisability of this behaviour.
            #  Hence insert this into the logic of the aws-sdk integration.
            "$..cause"
        ]
    )
    @pytest.mark.parametrize(
        "state_machine_template",
        [
            ST.load_sfn_template(ST.AWS_SDK_SFN_SEND_TASK_SUCCESS),
            ST.load_sfn_template(ST.AWS_SDK_SFN_SEND_TASK_FAILURE),
        ],
    )
    @markers.aws.validated
    def test_sfn_send_task_outcome_with_no_such_token(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
        state_machine_template,
    ):
        definition = json.dumps(state_machine_template)

        exec_input = json.dumps({"TaskToken": "NoSuchTaskToken"})
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    def test_sfn_start_execution(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
    ):
        template_target = BT.load_sfn_template(BT.BASE_RAISE_FAILURE)
        definition_target = json.dumps(template_target)
        state_machine_arn_target = create_state_machine_with_iam_role(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition_target,
        )

        template = ST.load_sfn_template(ST.AWS_SDK_SFN_START_EXECUTION)
        definition = json.dumps(template)

        exec_input = json.dumps(
            {"StateMachineArn": state_machine_arn_target, "Input": None, "Name": "TestStartTarget"}
        )
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    def test_sfn_start_execution_implicit_json_serialisation(
        self,
        aws_client,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
    ):
        sfn_snapshot.add_transformer(
            JsonpathTransformer(
                jsonpath="$..output.ExecutionArn",
                replacement="execution-arn",
                replace_reference=True,
            )
        )

        template_target = BT.load_sfn_template(BT.BASE_PASS_RESULT)
        definition_target = json.dumps(template_target)
        state_machine_arn_target = create_state_machine_with_iam_role(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition_target,
        )

        template = ST.load_sfn_template(ST.AWS_SDK_SFN_START_EXECUTION_IMPLICIT_JSON_SERIALISATION)
        template["States"]["StartTarget"]["Parameters"]["StateMachineArn"] = (
            state_machine_arn_target
        )
        definition = json.dumps(template)

        exec_input = json.dumps({})
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    @pytest.mark.parametrize(
        "file_body",
        ["", "text data", b"", b"binary data", bytearray(b"byte array data")],
        ids=["empty_str", "str", "empty_binary", "binary", "bytearray"],
    )
    # it seems the SFn internal client does not return the checksum values from the object yet, maybe it hasn't
    #  been updated to parse those fields?
    @markers.snapshot.skip_snapshot_verify(paths=["$..ChecksumCrc32", "$..ChecksumType"])
    def test_s3_get_object(
        self,
        aws_client,
        s3_create_bucket,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
        file_body,
    ):
        bucket_name = s3_create_bucket()
        sfn_snapshot.add_transformer(RegexTransformer(bucket_name, "bucket-name"))

        file_key = "file_key"
        aws_client.s3.put_object(Bucket=bucket_name, Key=file_key, Body=file_body)

        template = ST.load_sfn_template(ST.AWS_SDK_S3_GET_OBJECT)
        definition = json.dumps(template)

        exec_input = json.dumps({"Bucket": bucket_name, "Key": file_key})
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )

    @markers.aws.validated
    @markers.snapshot.skip_snapshot_verify(
        paths=[
            "$..ContentType",  # TODO: update the default ContentType
            # it seems the SFn internal client does not return the checksum values from the object yet, maybe it hasn't
            #  been updated to parse those fields?
            "$..ChecksumCrc32",  # returned by LocalStack, casing issue
            "$..ChecksumCRC32",  # returned by AWS
        ]
    )
    @pytest.mark.parametrize(
        "body",
        ["text data", {"Dict": "Value"}, ["List", "Data"], False, 0],
        ids=["str", "dict", "list", "bool", "num"],
    )
    def test_s3_put_object(
        self,
        aws_client,
        s3_create_bucket,
        create_state_machine_iam_role,
        create_state_machine,
        sfn_snapshot,
        body,
    ):
        file_key = f"file-key-{short_uid()}"
        bucket_name = s3_create_bucket()
        sfn_snapshot.add_transformer(RegexTransformer(file_key, "file-key"))
        sfn_snapshot.add_transformer(RegexTransformer(bucket_name, "bucket-name"))

        template = ST.load_sfn_template(ST.AWS_SDK_S3_PUT_OBJECT)
        definition = json.dumps(template)

        exec_input = json.dumps({"Bucket": bucket_name, "Key": file_key, "Body": body})
        create_and_record_execution(
            aws_client,
            create_state_machine_iam_role,
            create_state_machine,
            sfn_snapshot,
            definition,
            exec_input,
        )
        get_object_response = aws_client.s3.get_object(Bucket=bucket_name, Key=file_key)

        sfn_snapshot.match("get-s3-object", get_object_response)
