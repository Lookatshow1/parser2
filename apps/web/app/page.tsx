"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles, Rocket, BarChart3, Zap, ArrowRight, Check,
  Loader2, Globe, FileText, Image as ImageIcon, ChevronRight,
  Target, TrendingUp, Shield, Play, Star, Users, Clock,
  MousePointer, DollarSign, Flame, Award, CheckCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

// Types
interface AdCreative {
  title: string;
  text: string;
  approach: string;
}

interface ImageCreative {
  url: string;
  prompt: string;
  theme: string;
}

interface GeneratedCreatives {
  business_name: string;
  business_type: string;
  ads: AdCreative[];
  images: ImageCreative[];
}

// API call
async function generateCreatives(landingUrl: string, description: string): Promise<GeneratedCreatives> {
  const response = await fetch("/api/magic/generate-public", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ landing_url: landingUrl || null, description: description || null })
  });

  if (!response.ok) {
    throw new Error("Ошибка генерации");
  }

  return response.json();
}

// Floating particles component
function FloatingParticles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-violet-500/30 rounded-full animate-float"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${5 + Math.random() * 10}s`
          }}
        />
      ))}
    </div>
  );
}

// Animated counter
function AnimatedCounter({ value, suffix = "" }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  return <span>{count.toLocaleString('ru-RU')}{suffix}</span>;
}

export default function LandingPage() {
  const router = useRouter();
  const [landingUrl, setLandingUrl] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [creatives, setCreatives] = useState<GeneratedCreatives | null>(null);
  const [showInput, setShowInput] = useState<"url" | "text">("url");
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  const handleGenerate = async () => {
    if (!landingUrl && !description) {
      toast.error("Введите URL сайта или описание бизнеса");
      return;
    }

    setLoading(true);
    try {
      const result = await generateCreatives(landingUrl, description);
      setCreatives(result);

      localStorage.setItem("pending_creatives", JSON.stringify({
        creatives: result,
        landing_url: landingUrl
      }));

      toast.success("🎉 Креативы готовы!");
    } catch (error) {
      toast.error("Произошла ошибка. Попробуйте ещё раз.");
    } finally {
      setLoading(false);
    }
  };

  const handleLaunch = () => {
    router.push("/signup?from=magic");
  };

  const testimonials = [
    { name: "Александр К.", company: "Интернет-магазин", text: "Запустили рекламу за 10 минут. ROAS вырос в 3 раза!", avatar: "А" },
    { name: "Мария С.", company: "Салон красоты", text: "Наконец-то реклама, которая работает без агентства!", avatar: "М" },
    { name: "Дмитрий В.", company: "Автосервис", text: "AI создал объявления лучше, чем маркетолог за 50к/мес", avatar: "Д" }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#030014] text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-950/50 via-[#030014] to-fuchsia-950/30" />
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-violet-600/20 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-fuchsia-600/20 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/10 rounded-full blur-[150px]" />
        <FloatingParticles />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-2xl border-b border-white/5">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Effecto
            </span>
          </Link>
          <div className="flex gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-gray-300 hover:text-white hover:bg-white/10">
                Войти
              </Button>
            </Link>
            <Link href="/signup">
              <Button className="bg-white/10 hover:bg-white/20 backdrop-blur-xl border border-white/20">
                Регистрация
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-32 pb-20 px-4">
        <div className="container mx-auto text-center max-w-5xl">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 border border-violet-500/30 rounded-full px-5 py-2.5 mb-8 backdrop-blur-xl">
            <Flame className="h-4 w-4 text-orange-400" />
            <span className="text-sm font-medium bg-gradient-to-r from-violet-300 to-fuchsia-300 bg-clip-text text-transparent">
              AI-реклама нового поколения
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-6 leading-[1.1] tracking-tight">
            <span className="block bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">
              Реклама, которая
            </span>
            <span className="block mt-2 bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent animate-gradient">
              продаёт сама
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Введите URL или опишите бизнес — <span className="text-white font-medium">нейросеть создаст
              10 объявлений и 10 креативов</span> за 60 секунд
          </p>

          {/* Main Generator Card */}
          {!creatives ? (
            <div className="max-w-2xl mx-auto">
              {/* Input Type Selector */}
              <div className="flex gap-2 mb-6 justify-center">
                <button
                  onClick={() => setShowInput("url")}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${showInput === "url"
                      ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                    }`}
                >
                  <Globe className="h-4 w-4" />
                  URL сайта
                </button>
                <button
                  onClick={() => setShowInput("text")}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all ${showInput === "text"
                      ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                    }`}
                >
                  <FileText className="h-4 w-4" />
                  Описание
                </button>
              </div>

              {/* Input Card */}
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-3xl blur-xl opacity-30 group-hover:opacity-50 transition-opacity" />
                <div className="relative bg-white/5 backdrop-blur-2xl rounded-2xl p-8 border border-white/10">
                  {showInput === "url" ? (
                    <Input
                      placeholder="https://ваш-сайт.ru"
                      value={landingUrl}
                      onChange={(e) => setLandingUrl(e.target.value)}
                      className="text-lg h-14 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:ring-2 focus:ring-violet-500 mb-6"
                    />
                  ) : (
                    <Textarea
                      placeholder="Опишите ваш бизнес: чем занимаетесь, что продаёте, кто клиенты..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="min-h-[120px] bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:ring-2 focus:ring-violet-500 mb-6"
                    />
                  )}

                  <Button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 hover:from-violet-500 hover:via-fuchsia-500 hover:to-pink-500 rounded-xl shadow-lg shadow-violet-500/25 transition-all hover:shadow-xl hover:shadow-violet-500/30 hover:scale-[1.02]"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                        AI создаёт рекламу...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-3 h-5 w-5" />
                        Создать рекламу бесплатно
                        <ArrowRight className="ml-3 h-5 w-5" />
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Trust Badges */}
              <div className="flex flex-wrap items-center justify-center gap-6 mt-8 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Без регистрации
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-violet-400" />
                  60 секунд
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-400" />
                  Бесплатно
                </div>
              </div>
            </div>
          ) : (
            /* Results Section */
            <div className="max-w-6xl mx-auto">
              <div className="inline-flex items-center gap-2 bg-green-500/20 border border-green-500/30 rounded-full px-5 py-2.5 mb-8">
                <Check className="h-5 w-5 text-green-400" />
                <span className="text-green-300 font-medium">Ваши креативы готовы!</span>
              </div>

              {/* Ads Grid */}
              <h3 className="text-2xl font-bold mb-6 text-left flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-violet-400" />
                </div>
                10 текстовых объявлений
              </h3>
              <div className="grid md:grid-cols-2 gap-4 mb-12">
                {creatives.ads.map((ad, idx) => (
                  <div
                    key={idx}
                    className="group relative bg-white/5 backdrop-blur-xl rounded-xl p-5 border border-white/10 text-left hover:border-violet-500/50 transition-all hover:bg-white/10"
                  >
                    <div className="absolute top-3 right-3 px-2 py-1 rounded-md bg-violet-500/20 text-xs text-violet-300 font-medium">
                      {ad.approach}
                    </div>
                    <div className="font-semibold text-white mb-2 pr-20">{ad.title}</div>
                    <div className="text-gray-400 text-sm">{ad.text}</div>
                  </div>
                ))}
              </div>

              {/* Images Grid */}
              <h3 className="text-2xl font-bold mb-6 text-left flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 flex items-center justify-center">
                  <ImageIcon className="h-5 w-5 text-fuchsia-400" />
                </div>
                10 рекламных креативов
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-12">
                {creatives.images.map((img, idx) => (
                  <div
                    key={idx}
                    className="aspect-square rounded-xl overflow-hidden bg-white/5 border border-white/10 group hover:border-fuchsia-500/50 transition-all"
                  >
                    <img
                      src={img.url}
                      alt={img.theme}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                  </div>
                ))}
              </div>

              {/* CTA */}
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-3xl blur-xl opacity-40" />
                <div className="relative bg-gradient-to-r from-violet-900/50 to-fuchsia-900/50 backdrop-blur-xl border border-violet-500/30 rounded-2xl p-10">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <Rocket className="h-8 w-8 text-fuchsia-400" />
                  </div>
                  <h3 className="text-3xl font-bold mb-4">Запустите рекламу прямо сейчас</h3>
                  <p className="text-gray-400 mb-8 max-w-lg mx-auto">
                    Зарегистрируйтесь, пополните баланс от 1000₽ — ваши объявления начнут приводить клиентов
                  </p>
                  <Button
                    onClick={handleLaunch}
                    size="lg"
                    className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-lg px-10 h-14 rounded-xl shadow-lg shadow-violet-500/25"
                  >
                    <Rocket className="mr-3 h-5 w-5" />
                    Запустить рекламу
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 py-20 px-4 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: 127, suffix: "+", label: "Бизнесов", icon: Users },
              { value: 12, suffix: "M", label: "Показов", icon: Target },
              { value: 4.7, suffix: "x", label: "Средний ROAS", icon: TrendingUp },
              { value: 60, suffix: "сек", label: "На создание", icon: Clock }
            ].map((stat, idx) => (
              <div key={idx} className="text-center group">
                <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <stat.icon className="h-6 w-6 text-violet-400" />
                </div>
                <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-gray-500 mt-2">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 py-24 px-4 border-t border-white/5">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Всё для <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">роста бизнеса</span>
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Платформа, которая думает за вас и приводит клиентов на автопилоте
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Sparkles,
                color: "from-violet-600 to-violet-400",
                title: "AI-генерация",
                description: "Нейросеть анализирует ваш бизнес и создаёт тексты и креативы, которые продают"
              },
              {
                icon: Target,
                color: "from-fuchsia-600 to-fuchsia-400",
                title: "A/B тестирование",
                description: "Автоматически находим лучшие объявления. Статистическая значимость гарантирована"
              },
              {
                icon: DollarSign,
                color: "from-emerald-600 to-emerald-400",
                title: "Оптимизация бюджета",
                description: "AI перераспределяет бюджет на работающие кампании. ROAS растёт автоматически"
              }
            ].map((feature, idx) => (
              <div key={idx} className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-violet-600/10 to-fuchsia-600/10 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative bg-white/5 backdrop-blur-xl rounded-2xl p-8 border border-white/10 hover:border-white/20 transition-all h-full">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                    <feature.icon className="h-7 w-7 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-3 text-white">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="relative z-10 py-24 px-4 border-t border-white/5">
        <div className="container mx-auto max-w-4xl text-center">
          <div className="flex items-center justify-center gap-1 mb-6">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="h-6 w-6 text-yellow-400 fill-yellow-400" />
            ))}
          </div>

          <div className="relative h-48">
            {testimonials.map((t, idx) => (
              <div
                key={idx}
                className={`absolute inset-0 transition-all duration-500 ${idx === activeTestimonial
                    ? 'opacity-100 translate-y-0'
                    : 'opacity-0 translate-y-4'
                  }`}
              >
                <p className="text-2xl md:text-3xl font-medium text-white mb-6">
                  "{t.text}"
                </p>
                <div className="flex items-center justify-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center text-white font-bold">
                    {t.avatar}
                  </div>
                  <div className="text-left">
                    <div className="text-white font-medium">{t.name}</div>
                    <div className="text-gray-500 text-sm">{t.company}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveTestimonial(idx)}
                className={`w-2 h-2 rounded-full transition-all ${idx === activeTestimonial
                    ? 'w-8 bg-violet-500'
                    : 'bg-white/20'
                  }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative z-10 py-24 px-4">
        <div className="container mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-600/20 to-red-600/20 border border-orange-500/30 rounded-full px-5 py-2.5 mb-6">
            <Flame className="h-4 w-4 text-orange-400" />
            <span className="text-orange-300 text-sm font-medium">Присоединяйтесь к 100+ бизнесам</span>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Готовы получить <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">клиентов</span>?
          </h2>
          <p className="text-gray-400 text-lg mb-10">
            Создайте рекламу прямо сейчас — это бесплатно и займёт 60 секунд
          </p>
          <Button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            size="lg"
            className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-lg px-10 h-14 rounded-xl shadow-lg shadow-violet-500/25"
          >
            <Sparkles className="mr-3 h-5 w-5" />
            Создать рекламу
            <ArrowRight className="ml-3 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 px-4 border-t border-white/5">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span>© 2026 Effecto</span>
          </div>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition-colors">Политика конфиденциальности</a>
            <a href="#" className="hover:text-white transition-colors">Условия использования</a>
          </div>
        </div>
      </footer>

      {/* CSS for animations */}
      <style jsx global>{`
                @keyframes float {
                    0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.3; }
                    50% { transform: translateY(-20px) translateX(10px); opacity: 0.8; }
                }
                .animate-float {
                    animation: float 8s ease-in-out infinite;
                }
                @keyframes gradient {
                    0%, 100% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                }
                .animate-gradient {
                    background-size: 200% 200%;
                    animation: gradient 4s ease infinite;
                }
            `}</style>
    </div>
  );
}
