import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import axios from "axios";

interface UsageData {
  model: string;
  tokensUsed: number;
  costUSD: number;
  date: string;
}

const Dashboard = () => {
  const [usage, setUsage] = useState<UsageData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string>("all");

  useEffect(() => {
    const fetchUsage = async () => {
      setLoading(true);
      try {
        const response = await axios.get("/api/azure-openai/usage");
        setUsage(response.data);
      } catch (error) {
        console.error("Failed to fetch usage data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsage();
  }, []);

  const filteredUsage = selectedModel === "all"
    ? usage
    : usage.filter(u => u.model === selectedModel);

  const totalTokens = filteredUsage.reduce((acc, u) => acc + u.tokensUsed, 0);
  const totalCost = filteredUsage.reduce((acc, u) => acc + u.costUSD, 0);

  const models = Array.from(new Set(usage.map(u => u.model)));

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Azure OpenAI Usage Dashboard</h1>
      {loading ? (
        <div className="text-center text-gray-500">Loading usage data, please wait...</div>
      ) : (
        <Tabs defaultValue="all" className="w-full" onValueChange={setSelectedModel}>
          <TabsList>
            <TabsTrigger value="all">All Models</TabsTrigger>
            {models.map(model => (
              <TabsTrigger key={model} value={model}>{model}</TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={selectedModel}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="p-4">
                  <h2 className="text-lg font-semibold">Total Tokens Used</h2>
                  <p className="text-2xl font-bold text-blue-600">{totalTokens.toLocaleString()}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <h2 className="text-lg font-semibold">Total Cost (USD)</h2>
                  <p className="text-2xl font-bold text-green-600">${totalCost.toFixed(2)}</p>
                </CardContent>
              </Card>
            </div>
            <div className="mt-6 space-y-4">
              {filteredUsage.map((u, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <div className="flex justify-between">
                      <div>
                        <p className="font-semibold">{u.date}</p>
                        <p className="text-sm text-gray-500">Model: {u.model}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{u.tokensUsed.toLocaleString()} tokens</p>
                        <p className="text-green-600">${u.costUSD.toFixed(4)}</p>
                      </div>
                    </div>
                    <Progress value={(u.tokensUsed / totalTokens) * 100} className="mt-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default Dashboard;
