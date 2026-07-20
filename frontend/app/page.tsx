"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSessionId } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (getSessionId()) router.replace("/favorites");
    else router.replace("/login");
  }, [router]);
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full" />
    </div>
  );
}