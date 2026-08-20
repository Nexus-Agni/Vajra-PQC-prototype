# PHASE 1 REQUIREMENTS TRACEABILITY

| Requirement | Implementation File | Test File | Test Name | Execution Result | Evidence Artifact | Status |
|---|---|---|---|---|---|---|
| TransactionEnvelope | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_normal_envelope` | PASS | Unit test logs | PASS |
| TLP enum | `packages/qstie-common/qstie_common/enums/protocol_enums.py` | `tests/unit/test_envelope.py` | `test_normal_envelope` | PASS | Unit test logs | PASS |
| transaction states | `packages/qstie-common/qstie_common/enums/protocol_enums.py` | (Implicit in enum definitions) | N/A | PASS | Code inspect | PASS |
| ACK/NACK | `packages/qstie-common/qstie_common/enums/protocol_enums.py` | `tests/protocol/test_frame_codec.py` | `test_multiple_consecutive` | PASS | Unit test logs | PASS |
| NACK reasons | `packages/qstie-common/qstie_common/enums/protocol_enums.py` | (Implicit in enum definitions) | N/A | PASS | Code inspect | PASS |
| fingerprint utility | `packages/qstie-common/qstie_common/fingerprints/utils.py` | `tests/unit/test_envelope.py` | `test_fingerprint_preservation` | PASS | Unit test logs | PASS |
| protobuf schema | `proto/qstie.proto` | `tests/unit/test_envelope.py` | `test_normal_envelope` | PASS | `qstie_pb2.py` | PASS |
| protobuf round-trip | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_normal_envelope` | PASS | Unit test logs | PASS |
| frame encoder | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_single_round_trip` | PASS | Unit test logs | PASS |
| frame decoder | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_single_round_trip` | PASS | Unit test logs | PASS |
| maximum frame size | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_oversized_frame` | PASS | Unit test logs | PASS |
| empty envelope | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_empty_envelope` | PASS | Unit test logs | PASS |
| normal envelope | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_normal_envelope` | PASS | Unit test logs | PASS |
| large envelope | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_large_envelope` | PASS | Unit test logs | PASS |
| Unicode | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_unicode_fields` | PASS | Unit test logs | PASS |
| binary signature | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_binary_signature` | PASS | Unit test logs | PASS |
| UUID preservation | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_uuid_timestamp_preservation` | PASS | Unit test logs | PASS |
| timestamp preservation | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/unit/test_envelope.py` | `test_uuid_timestamp_preservation` | PASS | Unit test logs | PASS |
| multiple frames | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_multiple_consecutive` | PASS | Unit test logs | PASS |
| partial header | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_partial_header` | PASS | Unit test logs | PASS |
| partial payload | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_frame_codec.py` | `test_partial_payload` | PASS | Unit test logs | PASS |
| truncated frame | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/security/test_security.py` | `test_truncated_payload` | PASS | Unit test logs | PASS |
| oversized frame | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/security/test_security.py` | `test_oversized_actual_payload` | PASS | Unit test logs | PASS |
| invalid message type | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/security/test_security.py` | `test_invalid_message_type` | PASS | Unit test logs | PASS |
| invalid payload length | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/security/test_security.py` | `test_uint32_max_declared_length` | PASS | Unit test logs | PASS |
| malformed protobuf | `packages/qstie-common/qstie_common/models/envelope.py` | `tests/security/test_security.py` | `test_malformed_protobuf` | PASS | Unit test logs | PASS |
| random fragmentation | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/protocol/test_stream_fragmentation.py` | `test_random_fragmentation` | PASS | `repeated_validation.log` | PASS |
| golden vectors | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/regression/test_golden_vectors.py` | `test_golden_vectors` | PASS | `golden_vectors.json` | PASS |
| A→B interoperability | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/interoperability/test_interoperability.py` | `test_gateway_a_to_b` | PASS | Unit test logs | PASS |
| B→A interoperability | `packages/qstie-common/qstie_common/protocol/frame_codec.py` | `tests/interoperability/test_interoperability.py` | `test_gateway_b_to_a` | PASS | Unit test logs | PASS |
