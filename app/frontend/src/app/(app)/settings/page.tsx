"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { User, Settings, Bell, Shield, Monitor, Database } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").toUpperCase() || "SC";

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-h1 text-text-strong">Settings</h1>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="w-full justify-start gap-0 border-b border-border-subtle pb-0 rounded-none">
          {[
            { value: "profile", icon: User, label: "Profile" },
            { value: "preferences", icon: Settings, label: "Preferences" },
            { value: "notifications", icon: Bell, label: "Notifications" },
            { value: "security", icon: Shield, label: "Security" },
            { value: "display", icon: Monitor, label: "Display" },
            { value: "data", icon: Database, label: "Data" },
          ].map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="gap-2 data-[state=active]:border-b-2 data-[state=active]:border-primary-600 rounded-none px-4">
              <tab.icon className="w-4 h-4" />{tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="profile" className="mt-6">
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 space-y-6">
              <Card><CardHeader><CardTitle className="text-h4">Profile Information</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4 mb-4">
                    <Avatar className="h-16 w-16 rounded-xl"><AvatarFallback className="rounded-xl bg-primary-100 text-primary-700 text-[20px] font-bold">{initials}</AvatarFallback></Avatar>
                    <div><Button variant="outline" size="sm">Change Photo</Button></div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2"><Label>Full Name</Label><Input defaultValue={user?.full_name || "Dr. Sarah Chen"} /></div>
                    <div className="space-y-2"><Label>Email</Label><Input defaultValue="sarah.chen@hospital.com" type="email" /></div>
                    <div className="space-y-2"><Label>Department</Label><Select defaultValue="cardiology"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="cardiology">Cardiology</SelectItem><SelectItem value="neurology">Neurology</SelectItem></SelectContent></Select></div>
                    <div className="space-y-2"><Label>Role</Label><Input defaultValue="Attending Physician" disabled /></div>
                  </div>
                  <div className="flex justify-end gap-3 pt-2"><Button variant="outline">Cancel</Button><Button>Save Changes</Button></div>
                </CardContent>
              </Card>

              <Card><CardHeader><CardTitle className="text-h4">Preferences</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { label: "Default Patient View", desc: "Overview tab on patient selection" },
                    { label: "Evidence Panel", desc: "Show evidence panel by default" },
                    { label: "Auto-generate Summary", desc: "Generate AI summary when opening a patient" },
                    { label: "Confidence Warnings", desc: "Show warnings for low-confidence AI answers" },
                  ].map((pref, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0">
                      <div><p className="text-[13px] font-medium text-text-default">{pref.label}</p><p className="text-[12px] text-text-muted">{pref.desc}</p></div>
                      <Switch defaultChecked={i < 2} />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
            <div className="space-y-4">
              <Card><CardContent className="p-4"><h4 className="text-h4 text-text-strong mb-2">Quick Links</h4><div className="space-y-1">{[["Audit Log", "/audit"], ["API Keys", "#"], ["Documentation", "#"]].map(([l, h]) => <a key={l} href={h} className="block py-2 px-2 text-[13px] text-text-muted hover:text-primary-600 rounded hover:bg-bg-surface-tint">{l}</a>)}</div></CardContent></Card>
              <Card><CardContent className="p-4"><h4 className="text-h4 text-text-strong mb-2">Session Info</h4><div className="space-y-1.5 text-[12px]"><div className="flex justify-between"><span className="text-text-subtle">Last login</span><span className="text-text-default">May 15, 2025</span></div><div className="flex justify-between"><span className="text-text-subtle">Environment</span><span className="text-text-default">Synthetic Data</span></div></div></CardContent></Card>
            </div>
          </div>
        </TabsContent>

        {["preferences", "notifications", "security", "display", "data"].map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-6">
            <Card><CardContent className="py-12 text-center"><p className="text-body text-text-muted capitalize">{tab} settings panel</p></CardContent></Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
