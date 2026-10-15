const fs = require('fs');
const path = require('path');

const uploadDir = path.resolve(__dirname, '../upload');
const outputDir = path.resolve(__dirname, 'assets/azure-icons');

const wanted = {
  'all-resources.svg': '10001-icon-service-All-Resources',
  'disk.svg': '10032-icon-service-Disks',
  'snapshot.svg': '10026-icon-service-Disks-Snapshots',
  'extension.svg': '10799-icon-service-Extensions',
  'vm-scale-set.svg': '10034-icon-service-VM-Scale-Sets',
  'availability-set.svg': '10025-icon-service-Availability-Sets',
  'restore-point.svg': '02818-icon-service-Restore-Points-Collections',
  'image.svg': '10033-icon-service-Images',
  'compute-gallery.svg': '02864-icon-service-Azure-Compute-Galleries',
  'container-registry.svg': '10105-icon-service-Container-Registries',
  'container-instance.svg': '10104-icon-service-Container-Instances',
  'container-app.svg': '02884-icon-service-Worker-Container-App',
  'managed-identity.svg': '10227-icon-service-Managed-Identities',
  'recovery-vault.svg': '00017-icon-service-Recovery-Services-Vaults',
  'backup-vault.svg': '02361-icon-service-Backup-Vault',
  'network-interface.svg': '10080-icon-service-Network-Interfaces',
  'network-security-group.svg': '10067-icon-service-Network-Security-Groups',
  'public-ip.svg': '10069-icon-service-Public-IP-Addresses',
  'route-table.svg': '10082-icon-service-Route-Tables',
  'load-balancer.svg': '10062-icon-service-Load-Balancers',
  'application-gateway.svg': '10076-icon-service-Application-Gateways',
  'waf-policy.svg': '10362-icon-service-Web-Application-Firewall-Policies(WAF)',
  'private-dns.svg': '10064-icon-service-DNS-Zones',
  'network-watcher.svg': '10066-icon-service-Network-Watcher',
  'bastion.svg': '02422-icon-service-Bastions',
  'express-route.svg': '10079-icon-service-ExpressRoute-Circuits',
  'connection.svg': '10081-icon-service-Connections',
  'virtual-network-gateway.svg': '10063-icon-service-Virtual-Network-Gateways',
  'event-hub.svg': '00039-icon-service-Event-Hubs',
  'service-bus.svg': '10836-icon-service-Azure-Service-Bus',
  'log-analytics.svg': '00009-icon-service-Log-Analytics-Workspaces',
  'application-insights.svg': '00012-icon-service-Application-Insights',
  'monitor.svg': '00001-icon-service-Monitor',
  'alerts.svg': '00002-icon-service-Alerts',
  'automation.svg': '00022-icon-service-Automation-Accounts',
  'resource-graph.svg': '10318-icon-service-Resource-Graph-Explorer',
  'dashboard.svg': '10015-icon-service-Dashboard',
  'azure-arc.svg': '00756-icon-service-Azure-Arc',
  'arc-machine.svg': '01710-icon-service-Arc-Machines',
  'redis.svg': '10137-icon-service-Cache-Redis',
  'postgresql.svg': '10131-icon-service-Azure-Database-PostgreSQL-Server',
  'sql-server.svg': '10132-icon-service-SQL-Server',
  'ssh-key.svg': '00412-icon-service-SSH-Keys',
  'solution.svg': '00021-icon-service-Solutions',
  'migration.svg': '10281-icon-service-Azure-Migrate'
};

const found = new Map();
for (const file of fs.readdirSync(uploadDir).filter(name => /^\d{3} .*\.xml$/i.test(name)).sort()) {
  const raw = fs.readFileSync(path.join(uploadDir, file), 'utf8');
  const entries = JSON.parse(raw.slice(raw.indexOf('>') + 1, raw.lastIndexOf('<')));
  for (const entry of entries) {
    if (!entry.title || found.has(entry.title)) continue;
    const match = (entry.xml || '').match(/data:image\/svg\+xml,([^;\"]+)/);
    if (match) found.set(entry.title, Buffer.from(match[1], 'base64').toString('utf8'));
  }
}

fs.mkdirSync(outputDir, { recursive: true });
for (const [filename, title] of Object.entries(wanted)) {
  const svg = found.get(title);
  if (!svg) throw new Error(`Icon not found: ${title}`);
  fs.writeFileSync(path.join(outputDir, filename), svg);
}

console.log(`Extracted ${Object.keys(wanted).length} Azure icons.`);
