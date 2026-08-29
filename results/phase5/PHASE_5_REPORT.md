# VAJRA-PQC / QS-TIE
# PHASE 5 – DOCKERIZED SYSTEM TOPOLOGY – FINAL REPORT

## 1. Phase Objective
To integrate the complete Gateway A and Gateway B environments using a strict, Dockerized network topology. The objective was to create isolated subnets (`agency_a_net`, `tactical_a_net`, `tactical_b_net`, and `agency_b_net`) bridging only via a dedicated `netem-router`, proving that Gateway A cannot bypass the router to reach Gateway B during adverse network tests. Additionally, the real infrastructure (MISP and OpenCTI stacks) were deployed and stabilized.

## 2. Scope
- Containerizing and stabilizing real MISP (`mysql`, `misp`) and OpenCTI (`redis`, `elasticsearch`, `rabbitmq`, `minio`, `opencti`) deployments.
- Configuring a 4-network isolated topology using Docker bridge networks and statically assigned IPAM subnets to prevent collisions.
- Developing and deploying `netem-router` (based on Alpine with `iproute2`, `iptables`, `tc`) acting as the strict bridge between `tactical_a_net` and `tactical_b_net`.
- Verifying cross-network isolation and routing.
- Building scripts to toggle 'stable' and 'adverse' network delay profiles directly on the router interfaces.

## 3. Infrastructure & Environment Distinction (REAL vs MOCK)
As requested, this report explicitly distinguishes between real runtime implementations and mock dependencies used exclusively for testing.

### REAL Infrastructure:
- **MISP Source:** Real deployed MISP stack (`coolacid/misp-docker:core-latest` + `mysql:8`).
- **OpenCTI Sink:** Real deployed OpenCTI stack (`opencti/platform:6.3.3` + Redis + Elasticsearch + RabbitMQ + MinIO).
- **Gateway A & B:** Fully integrated Gateway containers executing inside strictly defined Docker bridge networks.
- **Routing Infrastructure:** Real `netem-router` container bridging exactly two tactical networks natively manipulating packets via `iptables` and Linux traffic control (`tc`).

### MOCK Infrastructure:
- None. Phase 5 entirely replaces the mock dependencies from Phase 4 with the real systems.

## 4. Evidence Gap Closure & Issue Resolutions
During the implementation, several critical roadblocks in the third-party infrastructure components were identified and resolved:

1. **ISSUE 1 (OpenCTI MinIO Secrets Constraints):** OpenCTI repeatedly crashed on boot due to `MINIO_ROOT_PASSWORD` requiring a minimum length of 8 characters. Resolved by setting robust dummy secrets (`opencti123`).
2. **ISSUE 2 (OpenCTI Elasticsearch Race Conditions):** OpenCTI failed instantly (`ECONNREFUSED`) if Elasticsearch was not fully initialized. Resolved by implementing a custom cluster-status `curl` healthcheck and `depends_on: service_healthy` enforcement.
3. **ISSUE 3 (OpenCTI Environment Variables for v6.3.3):** The base configuration used v5.x environment variables (`OPENCTI_ADMIN_EMAIL`), causing the Initialization checks to fail with "You need to configure the environment vars". Upgraded strictly to v6.x syntax (`APP__ADMIN__EMAIL`, `APP__ENCRYPTION_KEY`, `APP__BASE_URL`).
4. **ISSUE 4 (MISP SSL Certificate Boot Loop):** MISP's NGINX configuration crashed explicitly on boot expecting HTTPS certificates (`/etc/nginx/certs/cert.pem`). Resolved by securely mounting the prototype's PKI `gateway_raw` certificates into the container to enable native SSL.
5. **ISSUE 5 (MISP User Permissions Crash):** `misp-docker` crashed because `CRON_USER_ID` was omitted. Explicitly injected the required User ID to allow Supervisor to start properly.
6. **ISSUE 6 (Docker Subnet Overlap & DNS Disconnectedness):** Since `tactical_a_net` and `tactical_b_net` are physically disjointed, embedded Docker DNS failed to resolve Gateway B for Gateway A. Resolved by injecting explicit `extra_hosts` and installing `iproute2` into both Gateways, overriding their container Entrypoints to dynamically map static routes (`172.26.0.0/24 via 172.25.0.254`) forcing traffic exclusively over the `netem-router`.

## 5. Artifact Directory
Evidence generated in this phase revolves around configuration management and network state, captured via manual and automated tests documented within the tickets. The primary artifact is the fully stable `compose.yaml` and operational `toggle_router_profile.py`. (Further runtime JSON logs will be generated in Phase 6).

## 6. Final Decision

```text
PHASE 5 DECISION: GO
```
The foundation is fully integrated. Gateway A reaches Gateway B exclusively through the tactical router, successfully navigating independent, strictly partitioned subnets. The infrastructure dependencies (MISP and OpenCTI) are highly stable and survive restarts cleanly. The environment is now ready for Phase 6 (Pre-Benchmark Qualification & Failure Injection).
