# Cloud Providers: Deep Comparison

## Service Mapping

| Capability | AWS | GCP | Azure | Self-Host |
|-----------|-----|-----|-------|-----------|
| VMs | EC2 | Compute Engine | Virtual Machines | Any VPS (Hetzner, OVH) |
| Managed containers | ECS / Fargate | Cloud Run | Container Apps | Docker + Watchtower |
| Kubernetes | EKS | GKE | AKS | k3s, k0s |
| Serverless | Lambda | Cloud Functions | Functions | OpenFaaS, Knative |
| Object storage | S3 | Cloud Storage | Blob Storage | MinIO |
| Relational DB | RDS / Aurora | Cloud SQL / AlloyDB | SQL Database | Self-managed Postgres |
| NoSQL | DynamoDB | Firestore / Bigtable | Cosmos DB | MongoDB, ScyllaDB |
| Data warehouse | Redshift | BigQuery | Synapse | ClickHouse |
| ML platform | SageMaker | Vertex AI | Azure ML | Ollama, vLLM |
| CDN | CloudFront | Cloud CDN | Azure CDN | Cloudflare (works with any) |
| DNS | Route 53 | Cloud DNS | Azure DNS | Cloudflare DNS |
| Message queue | SQS / SNS | Pub/Sub | Service Bus | RabbitMQ, NATS |
| Secret manager | SSM / Secrets Manager | Secret Manager | Key Vault | Vault (HashiCorp) |
| IAM | IAM (verbose but powerful) | IAM (simpler model) | AD / RBAC | Roll your own (painful) |

## Pricing Models and Gotchas

### Universal Gotchas

These apply across all major clouds and catch people every time:

- **Egress fees**: Sending data OUT of a cloud costs money. Receiving is free. AWS charges ~$0.09/GB egress, GCP ~$0.08/GB, Azure ~$0.087/GB. This adds up fast with video, large API responses, or data pipelines.
- **NAT Gateway costs** (AWS): If you put services in a private subnet (you should for security), NAT Gateway costs ~$0.045/hr + $0.045/GB processed. A moderately busy app can rack up $100-400/mo just on the NAT Gateway. GCP's Cloud NAT is cheaper. Consider VPC endpoints for AWS services.
- **Cross-AZ traffic**: Data moving between availability zones costs ~$0.01/GB each way. Chatty microservices across AZs can generate surprising bills.
- **Idle resources**: Unused EBS volumes, unattached Elastic IPs, stopped-but-not-terminated instances, old snapshots. Set up billing alerts on day one.

### AWS Pricing

- **On-demand**: Full price, no commitment. Good for variable workloads.
- **Reserved Instances / Savings Plans**: 30-60% discount for 1-3 year commitment. Worth it for steady-state production workloads.
- **Spot Instances**: 60-90% discount, but can be terminated with 2 min notice. Good for batch, CI/CD, stateless workers.
- **Free tier**: 12 months of basics (t2.micro, 5GB S3, 750hr RDS). Watch the limits -- it's easy to accidentally exceed them.

### GCP Pricing

- **Sustained use discounts**: Automatic -- no commitment needed. Up to 30% off for consistent usage.
- **Committed use discounts**: 1-3 year commitment for bigger savings (similar to AWS RI).
- **Preemptible VMs**: Like Spot, 60-91% off, guaranteed terminated within 24h.
- **BigQuery**: Pay per query ($5/TB scanned) or flat-rate. Incredible for analytics but scan costs can surprise you.
- **Free tier**: More generous than AWS -- f1-micro always free, 5GB Cloud Storage always free.

### Azure Pricing

- **Reserved VMs**: Similar to AWS RI, 1-3 year terms.
- **Spot VMs**: Same concept as AWS/GCP spot.
- **Hybrid Benefit**: Bring your Windows Server / SQL Server licenses for up to 85% savings. This is Azure's killer feature for Microsoft shops.
- **Dev/Test pricing**: Discounted rates for non-production. Requires Visual Studio subscription.

## When Each Cloud Wins

### AWS Wins When

- You need breadth of services (200+ services, there's one for everything)
- You're hiring -- most cloud engineers know AWS
- You want the most mature ecosystem (largest partner network, most Stack Overflow answers)
- You need specific services that are AWS-only-good (e.g., DynamoDB, Lambda ecosystem, Step Functions)
- Compliance/government workloads (GovCloud is the most mature)

### GCP Wins When

- Data and ML are core to your product (BigQuery, Vertex AI, Dataflow)
- You want the best managed Kubernetes (GKE is measurably better than EKS)
- Your team values developer experience (GCP console is less overwhelming)
- You're heavy on containers and want simplicity (Cloud Run is excellent)
- You're using Firebase for mobile/web (tight integration)

### Azure Wins When

- Your org is already Microsoft (Active Directory, Office 365, .NET)
- You need enterprise features that integrate with existing Microsoft licensing
- Hybrid cloud is a real requirement (Azure Arc, Azure Stack)
- You can leverage Hybrid Benefit for significant savings
- Your customers/partners require Azure for compliance reasons

### Self-Hosting Wins When

- Cost predictability is critical (no surprise bills, fixed monthly cost)
- Data sovereignty requirements rule out US-owned clouds
- You have the ops team to manage infrastructure
- Your workload is compute-heavy and steady (GPU servers, game servers)
- You want to avoid vendor lock-in at the infrastructure layer
- Budget is tight and you can trade time for money (Hetzner dedicated servers are 5-10x cheaper than equivalent cloud VMs)

## Cost Estimation Rules of Thumb

### Small App (side project, early startup)

~$5-50/month
- Static frontend on Vercel/Netlify: $0
- Single container on Railway/Render: $5-25/mo
- Managed Postgres (smallest tier): $5-15/mo
- Domain + DNS: $10-15/yr

### Medium App (growing startup, 10K-100K users)

~$200-2,000/month
- 2-4 containers or App Runner / Cloud Run: $50-200/mo
- Managed Postgres (production-grade): $50-200/mo
- Redis cache: $15-50/mo
- CDN + storage: $10-50/mo
- Monitoring (Datadog, etc.): $50-200/mo
- NAT Gateway + networking (AWS): $100-400/mo -- this is the sneaky one

### Large App (established product, 100K+ users)

~$2,000-20,000+/month
- Kubernetes cluster or multi-service ECS: $500-3,000/mo
- Multi-AZ database (RDS, Aurora): $500-2,000/mo
- ElastiCache / Memorystore: $100-500/mo
- Load balancers + networking: $200-800/mo
- Monitoring + logging + APM: $300-1,000/mo
- WAF + security tooling: $100-500/mo
- Data transfer: varies wildly based on traffic patterns

## Multi-Cloud

**Usually not worth it.** Here's why:

- Double the IAM, networking, and operational knowledge
- Lowest common denominator limits what you can use from each cloud
- Terraform abstracts some differences, but not the important ones (IAM models, networking, managed service behaviors)
- "Avoiding vendor lock-in" sounds smart but the real lock-in is in your data and application architecture, not the cloud provider

**When it IS worth it:**
- CDN (Cloudflare) in front of any cloud -- always fine
- Specific best-of-breed services (e.g., AWS for compute + GCP BigQuery for analytics)
- Regulatory requirements mandating geographic redundancy across providers
- Acquired company runs on different cloud -- migration isn't immediate

**The pragmatic approach:** Pick one cloud, use it well, keep your architecture portable at the application layer (containers, standard protocols, abstracted storage interfaces). If you ever need to move, the migration cost is in your data and integrations, not in which cloud you're on.
