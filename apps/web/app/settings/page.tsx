"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { getOrgProfile, updateOrgProfile } from "../../lib/api";
import { STR } from "../../lib/strings";
import { applyTheme, getStoredTheme, setStoredTheme } from "../../lib/theme";

type OrgProfileForm = {
  legal_type: string;
  legal_name: string;
  inn: string;
  kpp: string;
  ogrn: string;
  ogrnip: string;
  legal_address: string;
  email_for_docs: string;
  phone: string;
  timezone: string;
  currency: string;
};

export default function SettingsPage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [profile, setProfile] = useState<OrgProfileForm | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    const current = getStoredTheme();
    setTheme(current);
    applyTheme(current);
  }, []);

  useEffect(() => {
    let active = true;
    async function loadProfile() {
      setLoadingProfile(true);
      try {
        const data = await getOrgProfile();
        if (!active) return;
        setProfile({
          legal_type: data.legal_type ?? "",
          legal_name: data.legal_name ?? "",
          inn: data.inn ?? "",
          kpp: data.kpp ?? "",
          ogrn: data.ogrn ?? "",
          ogrnip: data.ogrnip ?? "",
          legal_address: data.legal_address ?? "",
          email_for_docs: data.email_for_docs ?? "",
          phone: data.phone ?? "",
          timezone: data.timezone ?? "Europe/Moscow",
          currency: data.currency ?? "RUB",
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : STR.messages.error;
        toast.error(message);
      } finally {
        if (active) setLoadingProfile(false);
      }
    }
    loadProfile();
    return () => {
      active = false;
    };
  }, []);

  const handleTheme = (next: "dark" | "light") => {
    setTheme(next);
    setStoredTheme(next);
    applyTheme(next);
  };

  const handleProfileChange = (key: keyof OrgProfileForm, value: string) => {
    if (!profile) return;
    setProfile({ ...profile, [key]: value });
  };

  const handleSaveProfile = async () => {
    if (!profile) return;
    setSavingProfile(true);
    try {
      await updateOrgProfile({
        legal_type: profile.legal_type || null,
        legal_name: profile.legal_name || null,
        inn: profile.inn || null,
        kpp: profile.kpp || null,
        ogrn: profile.ogrn || null,
        ogrnip: profile.ogrnip || null,
        legal_address: profile.legal_address || null,
        email_for_docs: profile.email_for_docs || null,
        phone: profile.phone || null,
        timezone: profile.timezone || null,
        currency: profile.currency || null,
      });
      toast.success(STR.messages.orgProfileSaved);
    } catch (error) {
      const message = error instanceof Error ? error.message : STR.messages.error;
      toast.error(message);
    } finally {
      setSavingProfile(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{STR.labels.orgProfile}</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingProfile || !profile ? (
            <div className="text-sm text-muted">{STR.messages.loading}</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>{STR.labels.legalType}</Label>
                <Input
                  value={profile.legal_type}
                  onChange={(event) => handleProfileChange("legal_type", event.target.value)}
                  placeholder="ООО / ИП"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.legalName}</Label>
                <Input
                  value={profile.legal_name}
                  onChange={(event) => handleProfileChange("legal_name", event.target.value)}
                  placeholder="ООО «Демо»"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.inn}</Label>
                <Input
                  value={profile.inn}
                  onChange={(event) => handleProfileChange("inn", event.target.value)}
                  placeholder="7700000000"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.kpp}</Label>
                <Input
                  value={profile.kpp}
                  onChange={(event) => handleProfileChange("kpp", event.target.value)}
                  placeholder="770001001"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.ogrn}</Label>
                <Input
                  value={profile.ogrn}
                  onChange={(event) => handleProfileChange("ogrn", event.target.value)}
                  placeholder="1027700000000"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.ogrnip}</Label>
                <Input
                  value={profile.ogrnip}
                  onChange={(event) => handleProfileChange("ogrnip", event.target.value)}
                  placeholder="3047700000000"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>{STR.labels.legalAddress}</Label>
                <Input
                  value={profile.legal_address}
                  onChange={(event) => handleProfileChange("legal_address", event.target.value)}
                  placeholder="Москва, ул. Примерная, 1"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.emailForDocs}</Label>
                <Input
                  value={profile.email_for_docs}
                  onChange={(event) => handleProfileChange("email_for_docs", event.target.value)}
                  placeholder="docs@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.phone}</Label>
                <Input
                  value={profile.phone}
                  onChange={(event) => handleProfileChange("phone", event.target.value)}
                  placeholder="+7 999 000-00-00"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.timezone}</Label>
                <Input
                  value={profile.timezone}
                  onChange={(event) => handleProfileChange("timezone", event.target.value)}
                  placeholder="Europe/Moscow"
                />
              </div>
              <div className="space-y-2">
                <Label>{STR.labels.currency}</Label>
                <Input
                  value={profile.currency}
                  onChange={(event) => handleProfileChange("currency", event.target.value)}
                  placeholder="RUB"
                />
              </div>
              <div className="md:col-span-2">
                <Button onClick={handleSaveProfile} disabled={savingProfile}>
                  {savingProfile ? STR.messages.loading : STR.actions.save}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle>ИИ-настройки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm text-muted mb-4">
              Выберите модель для генерации рекламных кампаний с Magic Create.
            </div>

            <div className="space-y-2">
              <Label>Модель генерации</Label>
              <select className="w-full rounded-md border border-border bg-panel-strong px-3 py-2 text-sm text-text">
                <optgroup label="OpenAI">
                  <option value="chatgpt-5.2">ChatGPT 5.2 (Flagship)</option>
                  <option value="chatgpt-5.2-mini">ChatGPT 5.2 Mini (Быстрая)</option>
                  <option value="o3">o3 (Reasoning)</option>
                </optgroup>
                <optgroup label="Anthropic">
                  <option value="claude-opus-4.5">Claude Opus 4.5 (Мощная)</option>
                  <option value="claude-sonnet-4.5">Claude Sonnet 4.5 (Рекомендуемая)</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="gemini-3-pro">Gemini 3 Pro (Мультимодальная)</option>
                  <option value="gemini-3-flash">Gemini 3 Flash (Быстрая)</option>
                </optgroup>
                <optgroup label="Демо">
                  <option value="mock">Демо-режим (без API)</option>
                </optgroup>
              </select>
              <p className="text-xs text-muted">
                Модель влияет на качество и скорость генерации. Рекомендуем Claude Sonnet 4 или GPT-4.1.
              </p>
            </div>

            <div className="p-3 bg-accent/10 border border-accent/20 rounded-lg">
              <div className="text-sm font-medium text-accent mb-1">💡 Совет</div>
              <div className="text-xs text-muted">
                Для креативов высокого качества используйте GPT-4.1 или Claude Opus 4.
                Для быстрых тестов подойдёт GPT-4.1 Mini или Claude Haiku.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{STR.nav.settings}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 text-sm text-muted">
            <div>
              <div className="mb-2 font-medium text-text">{STR.labels.theme}</div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={theme === "dark" ? "default" : "secondary"}
                  size="sm"
                  onClick={() => handleTheme("dark")}
                >
                  {STR.labels.themeDark}
                </Button>
                <Button
                  variant={theme === "light" ? "default" : "secondary"}
                  size="sm"
                  onClick={() => handleTheme("light")}
                >
                  {STR.labels.themeLight}
                </Button>
              </div>
            </div>
            <div>Настройте внешний вид интерфейса. Остальные параметры будут добавлены позже.</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
