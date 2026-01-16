import { MagicWizard } from "@/components/magic/wizard";

export default function MagicPage() {
    return (
        <main className="min-h-screen pt-20 pb-20 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-20 pointer-events-none" />

            <div className="container relative z-10 mx-auto px-4">
                <div className="text-center mb-12">
                    <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-gray-400 mb-4 tracking-tight">
                        Ads Magic
                    </h1>
                    <p className="text-lg text-gray-400 max-w-2xl mx-auto">
                        Transform your landing page into a high-performing ad campaign in seconds using our advanced AI engine.
                    </p>
                </div>

                <MagicWizard />
            </div>
        </main>
    );
}
