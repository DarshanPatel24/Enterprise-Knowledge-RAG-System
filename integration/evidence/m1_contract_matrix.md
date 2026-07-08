# M1-S1 Contract Compatibility Matrix

| Contract | Producers | Consumers | Round-trip | Fork-free | Referenced by | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SecurityContext | ekcp | ekre, ekcp | yes | yes | ekre, ekcp | PASS | Injected by EKCP, enforced by EKRE ingress. |
| Citation | ekre | ekre, ekcp | yes | yes | ekre, ekcp | PASS | Produced by EKRE retrieval, consumed by EKCP. |
| RetrievalCandidate | ekre | ekre, ekcp | yes | yes | ekre, ekcp | PASS | Ranked evidence unit. |
| RetrievalContextPackage | ekre | ekcp | yes | yes | ekre, ekcp | PASS | EKRE -> EKCP retrieval handoff. |
| ExecutionContext | - | - | yes | yes | - | WARN | Defined; engines currently propagate ids via headers/context objects. |
| VectorCollectionRecord | ekie | ekre | yes | yes | ekre | PASS | Published by EKIE, inherited by EKRE; mirrored structurally today. |
| EnterpriseDataPurgeEvent | - | - | yes | yes | ekie | PASS | Defined; cross-service purge propagation pending (Master Integration M2-S2). |
