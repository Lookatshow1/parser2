"use client";

import { useEffect, useState } from "react";
import { BillingApi, BillingAccount } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CreditCard, Download, Plus } from "lucide-react";

export default function BillingPage() {
    const [account, setAccount] = useState<BillingAccount | null>(null);
    const [amount, setAmount] = useState("1000");

    useEffect(() => {
        loadBalance();
    }, []);

    const loadBalance = async () => {
        try {
            const acc = await BillingApi.getBalance();
            setAccount(acc);
        } catch (e) { console.error(e); }
    };

    const handleTopUp = async () => {
        try {
            await BillingApi.topTop(Number(amount));
            loadBalance();
            alert("Top-up successful!");
        } catch (e) { alert("Error processing payment"); }
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <h1 className="text-3xl font-bold mb-8">Billing & Finance</h1>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Balance Card */}
                <Card className="glass-card bg-gradient-to-br from-panel to-panel-strong border-white/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-gray-400">Current Balance</CardTitle>
                        <CreditCard className="h-4 w-4 text-accent" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-white">
                            {account ? `$${account.balance.toFixed(2)}` : "Loading..."}
                        </div>
                        <p className="text-xs text-gray-400 mt-1">
                            Available for ad spend
                        </p>
                    </CardContent>
                </Card>

                {/* Top Up Card */}
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle>Add Funds</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex gap-2">
                            <Input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                className="bg-black/20 border-white/10 text-white"
                            />
                            <Button onClick={handleTopUp} className="bg-accent hover:bg-accent/80">
                                <Plus className="mr-2 h-4 w-4" /> Top Up
                            </Button>
                        </div>
                        <p className="text-xs text-gray-500">
                            Mock payment gateway. Funds are added instantly.
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="mt-12">
                <h2 className="text-xl font-bold mb-4">Recent Invoices</h2>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-0">
                        <div className="p-4 text-center text-gray-500">
                            No invoices found.
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
