import { getSystemHealth, getActivityLogs, getMessagingTopology } from "@/lib/api/system";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/lib/utils";

export default async function ActivityPage() {
  const [healthResult, logsResult, topologyResult] = await Promise.allSettled([
    getSystemHealth(),
    getActivityLogs({ page: 1, page_size: 20 }),
    getMessagingTopology(),
  ]);

  const health = healthResult.status === "fulfilled" ? healthResult.value : null;
  const logs = logsResult.status === "fulfilled" ? logsResult.value.items : [];
  const topology = topologyResult.status === "fulfilled" ? topologyResult.value : null;

  const getServiceStatusVariant = (status: string) => {
    return status === "up" ? "success" : "error";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold font-headline tracking-tight text-[#131B2E]">
          System Status
        </h1>
        <p className="text-[#434655] mt-1">Monitor system health and activity logs</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {health ? (
          <>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${health.status === "healthy" ? "bg-[#007D55]" : health.status === "degraded" ? "bg-[#B45309]" : "bg-[#BA1A1A]"}`} />
                  <div>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Overall Status</p>
                    <p className="text-lg font-bold text-[#131B2E] capitalize">{health.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${health.services.database.status === "up" ? "bg-[#007D55]" : "bg-[#BA1A1A]"}`} />
                  <div>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Database</p>
                    <p className="text-lg font-bold text-[#131B2E] capitalize">{health.services.database.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${health.services.rabbitmq.status === "up" ? "bg-[#007D55]" : "bg-[#BA1A1A]"}`} />
                  <div>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">RabbitMQ</p>
                    <p className="text-lg font-bold text-[#131B2E] capitalize">{health.services.rabbitmq.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${health.services.redis.status === "up" ? "bg-[#007D55]" : "bg-[#BA1A1A]"}`} />
                  <div>
                    <p className="text-[10px] uppercase tracking-wider font-bold text-[#737686]">Redis</p>
                    <p className="text-lg font-bold text-[#131B2E] capitalize">{health.services.redis.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="col-span-4 flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        )}
      </div>

      {topology && (
        <Card>
          <CardContent className="p-6">
            <h2 className="font-headline text-lg font-bold text-[#131B2E] mb-4">Message Queue Topology</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-[#434655] mb-3">Queues</h3>
                <div className="space-y-2">
                  {topology.queues.map((queue) => (
                    <div key={queue.name} className="flex items-center justify-between p-3 bg-[#F2F3FF] rounded-lg">
                      <span className="text-sm font-mono text-[#131B2E]">{queue.name}</span>
                      <div className="flex items-center gap-4">
                        <Badge variant="info" size="sm">{queue.messages} messages</Badge>
                        <span className="text-xs text-[#737686]">{queue.consumers} consumers</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#434655] mb-3">Exchanges</h3>
                <div className="space-y-2">
                  {topology.exchanges.map((exchange) => (
                    <div key={exchange.name} className="flex items-center justify-between p-3 bg-[#F2F3FF] rounded-lg">
                      <span className="text-sm font-mono text-[#131B2E]">{exchange.name}</span>
                      <Badge variant="default" size="sm">{exchange.type}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card padding="none">
        <div className="p-6 border-b border-[#C3C6D7]/20">
          <h2 className="font-headline text-lg font-bold text-[#131B2E]">Recent Activity</h2>
        </div>
        <div className="divide-y divide-[#C3C6D7]/20">
          {logs.length === 0 ? (
            <div className="p-6 text-center text-[#434655]">No activity logs available</div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="p-4 flex items-start gap-4 hover:bg-[#F2F3FF] transition-colors">
                <div className="w-10 h-10 rounded-full bg-[#EAEDFF] flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-[#004AC6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[#131B2E]">{log.action}</p>
                  {log.details && <p className="text-sm text-[#434655] mt-1">{log.details}</p>}
                  {log.tender_id && (
                    <p className="text-xs text-[#737686] mt-1">Tender: {log.tender_id.slice(0, 8)}...</p>
                  )}
                </div>
                <span className="text-xs text-[#737686] whitespace-nowrap">
                  {formatDateTime(log.created_at)}
                </span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}