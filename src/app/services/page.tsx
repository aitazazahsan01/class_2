'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Code2, Smartphone, Brain, Globe } from "lucide-react"

export default function Component() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  const services = [
    {
      title: "Full Stack Development",
      description: "End-to-end web solutions using the latest technologies and frameworks.",
      icon: <Globe className="h-12 w-12 mb-4 text-primary" />,
    },
    {
      title: "App Development",
      description: "Native and cross-platform mobile applications for iOS and Android.",
      icon: <Smartphone className="h-12 w-12 mb-4 text-primary" />,
    },
    {
      title: "AI/ML Development",
      description: "Cutting-edge artificial intelligence and machine learning solutions.",
      icon: <Brain className="h-12 w-12 mb-4 text-primary" />,
    },
    {
      title: "Custom Software Solutions",
      description: "Tailored software to meet your specific business needs and challenges.",
      icon: <Code2 className="h-12 w-12 mb-4 text-primary" />,
    },
  ]

  return (
    <section className="relative w-full py-20 md:py-32 lg:py-48 overflow-hidden bg-gradient-to-br from-background to-secondary" aria-labelledby="services-title">
      <motion.div
        className="absolute inset-0 z-0"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute h-2 w-2 bg-primary rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            animate={{
              y: [0, -20, 0],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              repeatType: 'loop',
            }}
          />
        ))}
      </motion.div>
      <div className="container relative z-10 px-4 md:px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex flex-col items-center justify-center space-y-4 text-center"
        >
          <h2 id="services-title" className="text-4xl font-bold tracking-tighter sm:text-6xl bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
            Our Services
          </h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="max-w-[900px] text-muted-foreground sm:text-xl/relaxed"
          >
            Leveraging cutting-edge technologies to deliver innovative solutions across web, mobile, and AI domains.
          </motion.p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mx-auto grid max-w-5xl items-start gap-8 py-12 md:grid-cols-2 lg:gap-12"
        >
          {services.map((service, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 * index, duration: 0.6 }}
              whileHover={{ scale: 1.05 }}
              onHoverStart={() => setHoveredIndex(index)}
              onHoverEnd={() => setHoveredIndex(null)}
            >
              <Card className="relative w-full h-full overflow-hidden bg-card/50 backdrop-blur-sm border-primary/10">
                <CardHeader>
                  <motion.div
                    className="flex items-center justify-center"
                    animate={{ rotate: hoveredIndex === index ? 360 : 0 }}
                    transition={{ duration: 0.6 }}
                  >
                    {service.icon}
                  </motion.div>
                  <CardTitle className="text-2xl">{service.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-lg">{service.description}</CardDescription>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Button variant="outline" className="bg-background/50 backdrop-blur-sm">Learn More</Button>
                </CardFooter>
                <motion.div
                  className="absolute inset-0 bg-primary/10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: hoveredIndex === index ? 1 : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </Card>
            </motion.div>
          ))}
        </motion.div>
        <motion.div
          className="flex justify-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <Button size="lg" className="mt-8 bg-primary text-primary-foreground hover:bg-primary/90">
            <motion.span
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Get Started
            </motion.span>
          </Button>
        </motion.div>
      </div>
    </section>
  )
}