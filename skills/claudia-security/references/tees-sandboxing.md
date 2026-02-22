# TEEs, Sandboxing, and Isolation

## When You Need Isolation

- Running untrusted code (user-submitted, plugins, third-party)
- Processing sensitive data that shouldn't be visible to operators
- Multi-tenant systems where tenants shouldn't see each other's data
- Compliance requirements (HIPAA, PCI-DSS, SOC2)

## Sandboxing Options

### Process-Level Isolation

| Approach | Use Case | Security Level |
|----------|----------|---------------|
| Docker containers | Standard app isolation | Moderate (shared kernel) |
| gVisor | Untrusted workloads on shared infra | High (syscall filtering) |
| Firecracker microVMs | Serverless, multi-tenant | Very High (VM-level isolation) |
| WebAssembly (Wasm) | Plugin systems, edge compute | High (memory-safe sandbox) |
| V8 Isolates | JS plugin execution | High (Cloudflare Workers model) |

### Language-Level Sandboxing

- **Never use** `eval()` or `new Function()` for untrusted input
- **Node.js `vm` module**: NOT a security sandbox (docs say so explicitly)
- **Deno**: Permissions model (--allow-net, --allow-read) provides real sandboxing
- **WebAssembly**: True sandbox, no access to host unless explicitly granted

## Trusted Execution Environments (TEEs)

TEEs provide hardware-level isolation where even the machine operator can't see the data being processed.

### When to Use TEEs

- **Confidential computing**: Process data without the cloud provider seeing it
- **Multi-party computation**: Multiple parties compute on combined data without revealing inputs
- **AI inference on sensitive data**: Run models on private data with cryptographic guarantees
- **Key management**: Protect cryptographic keys even from privileged system access

### Available TEEs

| TEE | Provider | Notes |
|-----|----------|-------|
| Intel SGX | Intel CPUs | Enclaves, mature but being phased out for TDX |
| Intel TDX | Intel CPUs (newer) | VM-level isolation, newer and broader |
| AMD SEV-SNP | AMD CPUs | VM-level, good cloud support (Azure, GCP) |
| ARM CCA | ARM chips | Emerging, mobile/edge focus |
| AWS Nitro Enclaves | AWS | Simple TEE model, good for key management |
| Azure Confidential VMs | Azure | SEV-SNP or TDX based |

### TEE Limitations

- **Side-channel attacks**: TEEs have had vulnerabilities (Spectre, Foreshadow)
- **Attestation complexity**: Verifying the TEE is running your code is non-trivial
- **Performance overhead**: Encryption/decryption at memory boundaries
- **Supply chain trust**: You still trust the hardware manufacturer

### Practical Recommendation

For most applications, container isolation + network policies + encrypted storage is sufficient. TEEs are worth the complexity when you genuinely can't trust the infrastructure operator (multi-tenant SaaS, regulated data processing, confidential AI).

## Decision Framework

```
Do you run untrusted code?
├── Yes
│   ├── JavaScript → V8 Isolates or Deno with permissions
│   ├── Any language → Firecracker microVMs or gVisor
│   └── Plugins → WebAssembly
├── No, but multi-tenant
│   ├── Can trust infra operator → Containers + network policies
│   └── Can't trust infra operator → TEE (Nitro Enclaves, Confidential VMs)
└── No, single-tenant
    └── Standard containers are fine
```
