"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles, ArrowRight, Check, Loader2, Globe, FileText,
  Image as ImageIcon, Play, Star, Clock, Zap, X,
  MessageSquare, TrendingUp, Users, Shield, ChevronDown, Mic, MicOff
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

// =============================================================================
// TYPES
// =============================================================================

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

// =============================================================================
// API
// =============================================================================

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

// =============================================================================
// ANIMATED COUNTER
// =============================================================================

function AnimatedCounter({ value, suffix = "", duration = 2000 }: { value: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;

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
  }, [value, isVisible, duration]);

  return <span ref={ref}>{count.toLocaleString('ru-RU')}{suffix}</span>;
}

// =============================================================================
// MAIN LANDING PAGE
// =============================================================================

export default function LandingPage() {
  const router = useRouter();
  const [landingUrl, setLandingUrl] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [creatives, setCreatives] = useState<GeneratedCreatives | null>(null);
  const [inputMode, setInputMode] = useState<"url" | "text" | "voice">("url");
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  // Voice input state
  const [isRecording, setIsRecording] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Check for voice support on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setVoiceSupported('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);

      // Redirect if already logged in
      const token = window.localStorage.getItem("ads_access_token");
      if (token) {
        router.push("/magic-launch");
      }
    }
  }, [router]);

  // Voice recording handler
  const toggleVoiceRecording = () => {
    if (!voiceSupported) {
      toast.error("Голосовой ввод не поддерживается в вашем браузере");
      return;
    }

    if (isRecording) {
      // Stop recording
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    // Start recording
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;

    recognition.lang = 'ru-RU';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setIsRecording(true);
      setInputMode("voice");
      toast.info("🎤 Говорите... Расскажите про свой бизнес");
    };

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        setDescription(prev => prev + finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      toast.error("Ошибка распознавания голоса");
    };

    recognition.onend = () => {
      setIsRecording(false);
      if (description.trim()) {
        toast.success("✅ Голос распознан! Нажмите 'Создать рекламу'");
      }
    };

    recognition.start();
  };

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

      toast.success("Готово! AI создал вашу рекламу");
    } catch (error) {
      toast.error("Произошла ошибка. Попробуйте ещё раз.");
    } finally {
      setLoading(false);
    }
  };

  const testimonials = [
    {
      name: "Алексей Морозов",
      role: "Основатель интернет-магазина",
      text: "Раньше тратил 20 часов в неделю на рекламу. Теперь — 20 минут. Effecto делает всё сам.",
      result: "ROAS вырос с 2x до 5x",
      avatar: "А"
    },
    {
      name: "Екатерина Волкова",
      role: "Владелец салона красоты",
      text: "Я ничего не понимала в рекламе. Просто ввела сайт — и через час пошли заявки.",
      result: "+47 заявок за первую неделю",
      avatar: "Е"
    },
    {
      name: "Дмитрий Соколов",
      role: "Руководитель B2B компании",
      text: "Уволил агентство. Effecto работает лучше и стоит в 10 раз дешевле.",
      result: "Экономия 150 000₽/мес",
      avatar: "Д"
    }
  ];

  const faqs = [
    {
      q: "Как это работает без моего участия?",
      a: "Effecto AI анализирует ваш сайт, создаёт рекламные объявления, запускает их на Яндекс.Директ, VK и Ozon, а затем автоматически оптимизирует: отключает неэффективные, усиливает работающие, корректирует ставки 24/7."
    },
    {
      q: "Нужно ли разбираться в рекламе?",
      a: "Нет. Вся сложность скрыта под капотом. Вы просто указываете сайт или описываете бизнес — дальше AI делает всё сам. Это как нанять маркетолога, который никогда не спит и не ошибается."
    },
    {
      q: "Сколько стоит?",
      a: "Базовый тариф — 2 990₽/мес. Это в 10-50 раз дешевле агентства. Есть бесплатный период для тестирования."
    },
    {
      q: "Какие площадки поддерживаются?",
      a: "Яндекс.Директ, VK Реклама, Ozon Performance. Скоро добавим Google Ads и myTarget."
    },
    {
      q: "Что если реклама не сработает?",
      a: "AI постоянно тестирует разные подходы и находит то, что работает для вашего бизнеса. Если через 2 недели результатов нет — вернём деньги."
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[#09090b] text-white">
      {/* ================================================================= */}
      {/* HEADER */}
      {/* ================================================================= */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#09090b]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold">Effecto</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm text-zinc-400">
            <a href="#how" className="hover:text-white transition-colors">Как работает</a>
            <a href="#pricing" className="hover:text-white transition-colors">Цены</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white">
                Войти
              </Button>
            </Link>
            <Link href="/signup">
              <Button size="sm" className="bg-white text-black hover:bg-zinc-200">
                Начать бесплатно
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ================================================================= */}
      {/* HERO SECTION */}
      {/* ================================================================= */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Background gradients */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-violet-600/20 rounded-full blur-[120px]" />
          <div className="absolute top-40 left-1/4 w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[100px]" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center">
          {/* Trust badge */}
          <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-2 mb-8">
            <div className="flex -space-x-1">
              {["А", "М", "Д"].map((letter, i) => (
                <div key={i} className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-[10px] font-medium border-2 border-[#09090b]">
                  {letter}
                </div>
              ))}
            </div>
            <span className="text-sm text-zinc-400">127+ бизнесов уже на автопилоте</span>
          </div>

          {/* Main headline - JTBD focused */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block text-white">От сайта до клиентов</span>
            <span className="block mt-2 bg-gradient-to-r from-violet-400 via-fuchsia-400 to-violet-400 bg-clip-text text-transparent">
              за 60 секунд
            </span>
          </h1>

          {/* Value proposition - clear JTBD */}
          <p className="text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            <span className="text-white">Effecto AI</span> создаёт рекламу, запускает на всех площадках
            и оптимизирует 24/7. <span className="text-white">Вы получаете клиентов — без маркетолога и агентства.</span>
          </p>

          {/* Main CTA - Interactive demo */}
          {!creatives ? (
            <div className="max-w-xl mx-auto">
              {/* Input toggle */}
              <div className="flex justify-center gap-2 mb-4">
                <button
                  onClick={() => setInputMode("url")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${inputMode === "url"
                    ? "bg-white text-black font-medium"
                    : "text-zinc-400 hover:text-white"
                    }`}
                >
                  <Globe className="h-4 w-4" />
                  URL сайта
                </button>
                <button
                  onClick={() => setInputMode("text")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${inputMode === "text"
                    ? "bg-white text-black font-medium"
                    : "text-zinc-400 hover:text-white"
                    }`}
                >
                  <FileText className="h-4 w-4" />
                  Описание
                </button>
                {voiceSupported && (
                  <button
                    onClick={toggleVoiceRecording}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${inputMode === "voice" || isRecording
                      ? "bg-gradient-to-r from-red-500 to-orange-500 text-white font-medium"
                      : "text-zinc-400 hover:text-white"
                      }`}
                  >
                    {isRecording ? (
                      <>
                        <MicOff className="h-4 w-4 animate-pulse" />
                        Стоп
                      </>
                    ) : (
                      <>
                        <Mic className="h-4 w-4" />
                        Голосом
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Input form */}
              <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-6 border border-white/10">
                {inputMode === "url" ? (
                  <Input
                    placeholder="https://ваш-сайт.ru"
                    value={landingUrl}
                    onChange={(e) => setLandingUrl(e.target.value)}
                    className="h-14 text-lg bg-white/5 border-white/10 text-white placeholder:text-zinc-500 rounded-xl mb-4"
                  />
                ) : inputMode === "voice" ? (
                  <div className="mb-4">
                    {/* Voice recording animation */}
                    {isRecording && (
                      <div className="flex items-center justify-center gap-3 mb-4 py-4">
                        <div className="relative">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center animate-pulse">
                            <Mic className="h-8 w-8 text-white" />
                          </div>
                          <div className="absolute inset-0 w-16 h-16 rounded-full bg-red-500/30 animate-ping" />
                        </div>
                        <span className="text-white font-medium">Слушаю... Расскажите о бизнесе</span>
                      </div>
                    )}
                    <Textarea
                      placeholder={isRecording ? "🎤 Ваша речь появится здесь..." : "Надиктуйте или введите текст вручную"}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="min-h-[100px] bg-white/5 border-white/10 text-white placeholder:text-zinc-500 rounded-xl"
                    />
                    {!isRecording && description && (
                      <div className="text-xs text-green-400 mt-2">✓ Текст записан. Нажмите "Создать рекламу"</div>
                    )}
                  </div>
                ) : (
                  <Textarea
                    placeholder="Опишите бизнес: что продаёте, кто клиенты..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="min-h-[100px] bg-white/5 border-white/10 text-white placeholder:text-zinc-500 rounded-xl mb-4"
                  />
                )}

                <Button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 rounded-xl"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      AI создаёт рекламу...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-5 w-5" />
                      Создать рекламу бесплатно
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </>
                  )}
                </Button>
              </div>

              {/* Trust indicators */}
              <div className="flex flex-wrap justify-center gap-6 mt-6 text-sm text-zinc-500">
                <span className="flex items-center gap-1.5">
                  <Check className="h-4 w-4 text-green-500" />
                  Без регистрации
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-violet-400" />
                  60 секунд
                </span>
                <span className="flex items-center gap-1.5">
                  <Shield className="h-4 w-4 text-blue-400" />
                  Бесплатно
                </span>
              </div>
            </div>
          ) : (
            /* Results */
            <div className="max-w-4xl mx-auto">
              <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-full px-4 py-2 mb-8">
                <Check className="h-5 w-5 text-green-400" />
                <span className="text-green-400 font-medium">AI создал вашу рекламу</span>
              </div>

              {/* Ads preview */}
              <div className="grid sm:grid-cols-2 gap-4 mb-8 text-left">
                {creatives.ads.slice(0, 4).map((ad, idx) => (
                  <div key={idx} className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <div className="text-xs text-violet-400 mb-2">{ad.approach}</div>
                    <div className="font-semibold text-white mb-1">{ad.title}</div>
                    <div className="text-sm text-zinc-400">{ad.text}</div>
                  </div>
                ))}
              </div>

              {/* Images preview */}
              {creatives.images.length > 0 && (
                <div className="flex justify-center gap-3 mb-8">
                  {creatives.images.slice(0, 4).map((img, idx) => (
                    <div key={idx} className="w-20 h-20 rounded-lg overflow-hidden bg-white/5 border border-white/10">
                      <img src={img.url} alt="" className="w-full h-full object-cover" />
                    </div>
                  ))}
                </div>
              )}

              {/* CTA to continue */}
              <Button
                onClick={() => router.push("/signup?from=magic")}
                size="lg"
                className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
              >
                Запустить эту рекламу
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <p className="text-sm text-zinc-500 mt-3">
                Реклама запустится на Яндекс, VK и Ozon автоматически
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ================================================================= */}
      {/* PROBLEM SECTION - Agitation */}
      {/* ================================================================= */}
      <section className="py-20 px-4 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Реклама отнимает <span className="text-red-400">слишком много</span>
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Знакомо? Вы хотите клиентов, но...
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                problem: "Агентства берут 50-150К/мес",
                pain: "И всё равно нужно контролировать и объяснять",
                icon: "💸"
              },
              {
                problem: "Самому разбираться — это недели",
                pain: "Пока учишься — конкуренты уже продают",
                icon: "⏰"
              },
              {
                problem: "Фрилансеры пропадают",
                pain: "Или делают 'как у всех', без понимания вашего бизнеса",
                icon: "🤷"
              }
            ].map((item, idx) => (
              <div key={idx} className="bg-white/5 rounded-2xl p-6 border border-white/5">
                <div className="text-4xl mb-4">{item.icon}</div>
                <div className="text-lg font-medium text-white mb-2">{item.problem}</div>
                <div className="text-zinc-500">{item.pain}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* SOLUTION - How Effecto AI works */}
      {/* ================================================================= */}
      <section id="how" className="py-20 px-4 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/30 rounded-full px-4 py-2 mb-6">
              <Sparkles className="h-4 w-4 text-violet-400" />
              <span className="text-sm text-violet-300">Effecto AI</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Один AI. <span className="text-violet-400">Вся реклама.</span>
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Effecto AI — это не просто инструмент. Это ваш персональный маркетолог, который работает 24/7 и никогда не устаёт.
            </p>
          </div>

          {/* Steps */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {[
              {
                step: "01",
                title: "Вы даёте URL",
                description: "Просто вставьте ссылку на сайт или опишите бизнес в двух предложениях",
                time: "10 сек"
              },
              {
                step: "02",
                title: "AI создаёт рекламу",
                description: "Анализирует сайт, конкурентов, генерирует тексты, картинки и стратегию",
                time: "50 сек"
              },
              {
                step: "03",
                title: "Клиенты приходят",
                description: "Реклама работает на всех площадках, AI оптимизирует её каждый час",
                time: "24/7"
              }
            ].map((item, idx) => (
              <div key={idx} className="relative">
                <div className="text-6xl font-bold text-white/5 mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-zinc-400 mb-3">{item.description}</p>
                <div className="inline-flex items-center gap-1.5 text-sm text-violet-400">
                  <Clock className="h-3.5 w-3.5" />
                  {item.time}
                </div>
                {idx < 2 && (
                  <div className="hidden md:block absolute top-8 -right-4 text-zinc-700">
                    <ArrowRight className="h-6 w-6" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* AI Capabilities */}
          <div className="bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 rounded-3xl p-8 border border-white/10">
            <h3 className="text-xl font-semibold text-center mb-8">Что умеет Effecto AI</h3>
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { icon: "✍️", title: "Пишет тексты", desc: "Заголовки, объявления, призывы" },
                { icon: "🎨", title: "Создаёт картинки", desc: "Баннеры и креативы" },
                { icon: "📊", title: "Оптимизирует", desc: "Ставки, бюджеты, таргетинг" },
                { icon: "🔄", title: "Работает 24/7", desc: "Без выходных и перерывов" }
              ].map((cap, idx) => (
                <div key={idx} className="text-center">
                  <div className="text-3xl mb-3">{cap.icon}</div>
                  <div className="font-medium text-white">{cap.title}</div>
                  <div className="text-sm text-zinc-400">{cap.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* SOCIAL PROOF */}
      {/* ================================================================= */}
      <section className="py-20 px-4 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
            {[
              { value: 127, suffix: "+", label: "Бизнесов" },
              { value: 4.7, suffix: "x", label: "Средний ROAS" },
              { value: 23, suffix: "%", label: "Экономия бюджета" },
              { value: 15, suffix: " млн", label: "Показов в месяц" }
            ].map((stat, idx) => (
              <div key={idx} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-zinc-500">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Testimonials */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Что говорят клиенты</h2>
          </div>

          <div className="relative max-w-2xl mx-auto">
            {testimonials.map((t, idx) => (
              <div
                key={idx}
                className={`transition-all duration-500 ${idx === activeTestimonial ? 'opacity-100' : 'opacity-0 absolute inset-0'
                  }`}
              >
                <div className="bg-white/5 rounded-2xl p-8 border border-white/10">
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-5 w-5 text-yellow-400 fill-yellow-400" />
                    ))}
                  </div>
                  <p className="text-xl text-white mb-6">"{t.text}"</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-lg font-medium">
                        {t.avatar}
                      </div>
                      <div>
                        <div className="font-medium text-white">{t.name}</div>
                        <div className="text-sm text-zinc-400">{t.role}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-medium">{t.result}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Dots */}
            <div className="flex justify-center gap-2 mt-6">
              {testimonials.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveTestimonial(idx)}
                  className={`h-2 rounded-full transition-all ${idx === activeTestimonial ? 'w-8 bg-violet-500' : 'w-2 bg-white/20'
                    }`}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* PRICING */}
      {/* ================================================================= */}
      <section id="pricing" className="py-20 px-4 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Дешевле агентства в <span className="text-violet-400">10 раз</span>
            </h2>
            <p className="text-zinc-400 text-lg">
              Прозрачные цены. Без скрытых платежей.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Free */}
            <div className="bg-white/5 rounded-2xl p-8 border border-white/10">
              <div className="text-lg font-medium text-white mb-2">Старт</div>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">0₽</span>
                <span className="text-zinc-400">/мес</span>
              </div>
              <p className="text-zinc-400 text-sm mb-6">Для тестирования</p>
              <ul className="space-y-3 mb-8">
                {["1 рекламный кабинет", "10 AI-генераций", "Базовая аналитика"].map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-zinc-300">
                    <Check className="h-4 w-4 text-green-400" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button variant="outline" className="w-full" onClick={() => router.push("/signup")}>
                Начать бесплатно
              </Button>
            </div>

            {/* Pro */}
            <div className="bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 rounded-2xl p-8 border-2 border-violet-500/50 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                Популярный
              </div>
              <div className="text-lg font-medium text-white mb-2">Бизнес</div>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">2 990₽</span>
                <span className="text-zinc-400">/мес</span>
              </div>
              <p className="text-zinc-400 text-sm mb-6">Полный автопилот</p>
              <ul className="space-y-3 mb-8">
                {[
                  "5 рекламных кабинетов",
                  "Безлимитные AI-генерации",
                  "Автопилот 24/7",
                  "Умные ставки",
                  "Telegram-уведомления",
                  "Приоритетная поддержка"
                ].map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-zinc-300">
                    <Check className="h-4 w-4 text-green-400" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600" onClick={() => router.push("/signup")}>
                Выбрать план
              </Button>
            </div>
          </div>

          <p className="text-center text-sm text-zinc-500 mt-8">
            Нужно больше? <a href="mailto:hello@effecto.ru" className="text-violet-400 hover:underline">Напишите нам</a> — обсудим индивидуальные условия
          </p>
        </div>
      </section>

      {/* ================================================================= */}
      {/* FAQ */}
      {/* ================================================================= */}
      <section id="faq" className="py-20 px-4 border-t border-white/5">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Частые вопросы</h2>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left"
                >
                  <span className="font-medium text-white">{faq.q}</span>
                  <ChevronDown className={`h-5 w-5 text-zinc-400 transition-transform ${openFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === idx && (
                  <div className="px-6 pb-4 text-zinc-400">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* FINAL CTA */}
      {/* ================================================================= */}
      <section className="py-20 px-4 border-t border-white/5">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Готовы получать клиентов?
          </h2>
          <p className="text-zinc-400 text-lg mb-8">
            Попробуйте бесплатно. AI создаст рекламу за 60 секунд.
          </p>
          <Button
            size="lg"
            className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-lg h-14 px-8"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <Sparkles className="mr-2 h-5 w-5" />
            Начать бесплатно
          </Button>
        </div>
      </section>

      {/* ================================================================= */}
      {/* FOOTER */}
      {/* ================================================================= */}
      <footer className="py-8 px-4 border-t border-white/5">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-zinc-500">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
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
    </div>
  );
}
