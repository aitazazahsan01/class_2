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

    <div>
      <Component2/>
    
        <br />
        <div className="flex justify-center ">
          <Card>
              <CardHeader>
                <CardTitle>Application Form</CardTitle>
              <CardDescription>Im filling this card for applying in this job</CardDescription>
              </CardHeader>

              <CardContent>
                <input type="text" placeholder="Enter ur Name" className="border-2  border-black"/>
                <br />
                <input type="number" placeholder="Enter ur Age" className="border-2 border-black mt-5"/>
                <br />
                <input type="email" placeholder="Enter ur Email" className="border-2 border-black mt-5"/>
                <br />
                <Button className="mt-5 ml-12 hover:shadow-lg hover:shadow-blue-400">SUBMIT</Button>
              </CardContent>
              <CardFooter>
                Wait Till You Get any Response from ur Side
              </CardFooter>
          </Card>
        </div>

          <div className="flex justify-center my-12">
            <HoverCard>
            <HoverCardTrigger>Hover Here</HoverCardTrigger>
            <HoverCardContent>
              Hello I have imported Hover Card from ShadCN UI
            </HoverCardContent>
          </HoverCard>
          </div>
          <div className="flex justify-center">
            <Component/>
          </div>
    </div>
  );
}
