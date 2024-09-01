'use client'
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import React, { useState } from "react";
import Component from "../../components/cardgpt";
import Component2 from "../../components/navbar";

export default function Home() {

  const [date, setDate] = useState(24);
  return (

    <><h1>Landing Page</h1></>
  );
}
