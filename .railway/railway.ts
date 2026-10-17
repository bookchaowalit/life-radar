import { defineRailway, project, service } from "railway/iac";

// life-radar: the Life Radar cell. Variables stay unmanaged (secrets live in Railway only).
// radar-api sleeps when idle (Railway Serverless) and wakes on the next request.
// Every service runs in Singapore next to Neon (aws-ap-southeast-1) and empire-platform; the IaC does not
// carry the region, so after the first deploy: railway scale --service <svc> asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0
// Not applied yet: provisioning and the first deploy wait for the owner's approval.
export default defineRailway(() => {
  const api = service("radar-api", {
    healthcheck: "/health",
    healthcheckTimeout: 60,
    deploy: { sleepApplication: true },
  });

  return project("life-radar", {
    variables: { managed: false },
    resources: [api],
  });
});
