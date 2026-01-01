\"use client\";

import { useState } from \"react\";
import { seedDev } from \"../lib/api\";

export default function HomePage() {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleSeed = async () => {
    setError(null);
    setNotice(null);
    try {
      const data = await seedDev();
      setNotice(`Seeded advertiser ${data.advertiser_id}, plan ${data.plan_id}, experiment ${data.experiment_id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className=\"card space-y-4\">
      <div>
        <h1 className=\"text-2xl font-semibold mb-2\">Ads Aggregator Admin</h1>
        <p className=\"text-slate-300\">Use navigation to manage connections, plans, and experiments.</p>
      </div>
      {error && <div className=\"text-red-400\">{error}</div>}
      {notice && <div className=\"text-green-400\">{notice}</div>}
      <button onClick={handleSeed}>Seed</button>
    </div>
  );
}
