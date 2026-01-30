"use client";

import { useEffect, useState } from "react";
import { BillingApi, BillingAccount, BillingTransaction } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CreditCard, Plus, ArrowUpRight, ArrowDownLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { STR } from "@/lib/strings";


export default function BillingPage() {
    const [account, setAccount] = useState<BillingAccount | null>(null);
    const [transactions, setTransactions] = useState<BillingTransaction[]>([]);
    const [amount, setAmount] = useState("1000");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [acc, txs] = await Promise.all([
                BillingApi.getBalance(),
                BillingApi.getTransactions()
            ]);
            setAccount(acc);
            setTransactions(txs);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleTopUp = async () => {
        try {
            await BillingApi.topUp(Number(amount));
            toast.success(`₽${Number(amount).toLocaleString('ru-RU')} ${STR.billing.topUpSuccess.toLowerCase()}`);
            loadData();
        } catch (e) { toast.error(STR.billing.topUpError); }
    };


    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-4 container mx-auto text-white">
            <h1 className="text-3xl font-bold mb-8">{STR.billing.title}</h1>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Balance Card */}
                <Card className="glass-card bg-gradient-to-br from-panel to-panel-strong border-white/5">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-gray-400">{STR.billing.balance}</CardTitle>
                        <CreditCard className="h-4 w-4 text-accent" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold text-white">
                            {account ? `₽${Number(account.balance).toLocaleString('ru-RU')}` : STR.messages.loading}
                        </div>
                        <p className="text-xs text-gray-400 mt-1">
                            {STR.billing.balanceHint}
                        </p>
                    </CardContent>
                </Card>

                {/* Top Up Card */}
                <Card className="glass-card border-white/5">
                    <CardHeader>
                        <CardTitle>{STR.billing.addFunds}</CardTitle>
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
                                <Plus className="mr-2 h-4 w-4" /> {STR.billing.topUp}
                            </Button>
                        </div>

                        {/* YooKassa Payment Button */}
                        <div className="pt-3 border-t border-white/10">
                            <Button
                                variant="outline"
                                className="w-full border-success/50 text-success hover:bg-success/10"
                                onClick={async () => {
                                    try {
                                        const token = localStorage.getItem("ads_access_token");
                                        const res = await fetch(`/api/payments/create`, {
                                            method: "POST",
                                            headers: {
                                                "Content-Type": "application/json",
                                                "Authorization": `Bearer ${token}`
                                            },
                                            body: JSON.stringify({ amount: Number(amount) })
                                        });
                                        const data = await res.json();

                                        if (data.confirmation_url) {
                                            window.location.href = data.confirmation_url;
                                        } else if (data.demo_mode) {
                                            toast.info("YooKassa не настроен. Используйте демо-пополнение.");
                                        } else if (data.error) {
                                            toast.error(data.error);
                                        }
                                    } catch (e) {
                                        toast.error("Ошибка создания платежа");
                                    }
                                }}
                            >
                                <CreditCard className="mr-2 h-4 w-4" />
                                Оплатить картой (YooKassa)
                            </Button>
                        </div>

                        <p className="text-xs text-gray-500">
                            {STR.billing.addFundsHint}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Transactions */}
            <div className="mt-12">
                <h2 className="text-xl font-bold mb-4">{STR.billing.transactions}</h2>
                <Card className="glass-card border-white/5">
                    <CardContent className="p-0">
                        {loading ? (
                            <div className="p-8 flex justify-center">
                                <Loader2 className="w-6 h-6 text-accent animate-spin" />
                            </div>
                        ) : transactions.length === 0 ? (
                            <div className="p-8 text-center text-gray-500">
                                {STR.billing.noTransactions}
                            </div>
                        ) : (
                            <div className="divide-y divide-white/5">
                                {transactions.map((tx) => (
                                    <div key={tx.id} className="p-4 flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${tx.type === 'topup' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                                }`}>
                                                {tx.type === 'topup' ?
                                                    <ArrowDownLeft className="h-4 w-4" /> :
                                                    <ArrowUpRight className="h-4 w-4" />
                                                }
                                            </div>
                                            <div>
                                                <div className="font-medium text-white capitalize">
                                                    {tx.type === 'topup' ? 'Пополнение' : tx.type === 'spend' ? 'Списание' : tx.type}
                                                </div>
                                                <div className="text-xs text-gray-500">{formatDate(tx.created_at)}</div>
                                            </div>
                                        </div>
                                        <div className={`font-semibold ${tx.type === 'topup' ? 'text-green-400' : 'text-red-400'}`}>
                                            {tx.type === 'topup' ? '+' : '-'}₽{Number(tx.amount).toLocaleString('ru-RU')}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
