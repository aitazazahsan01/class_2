'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const products = [
  { id: 1, name: "Eco-Friendly Water Bottle", price: "$24.99", badge: "New" },
  { id: 2, name: "Wireless Earbuds", price: "$79.99", badge: "Popular" },
  { id: 3, name: "Smart Watch", price: "$199.99", badge: "Featured" },
  { id: 4, name: "Organic Cotton T-Shirt", price: "$29.99" },
  { id: 5, name: "Noise-Cancelling Headphones", price: "$249.99", badge: "Sale" },
  { id: 6, name: "Portable Charger", price: "$39.99" },
]

export default function AnimatedProducts() {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  })

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
    },
  }

  return (
    <div className="container mx-auto px-4 py-16">
      <h2 className="text-3xl font-bold text-center mb-12">Our Products</h2>
      <motion.div
        ref={ref}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        variants={containerVariants}
        initial="hidden"
        animate={inView ? "visible" : "hidden"}
      >
        {products.map((product) => (
          <motion.div key={product.id} variants={itemVariants}>
            <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg">
              <CardHeader className="p-0">
                <div className="aspect-video bg-muted relative">
                  <img
                    src={`/placeholder.svg?height=250&width=500&text=${product.name}`}
                    alt={product.name}
                    className="object-cover w-full h-full"
                  />
                  {product.badge && (
                    <Badge className="absolute top-2 right-2">{product.badge}</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <CardTitle className="text-lg mb-2">{product.name}</CardTitle>
                <p className="text-muted-foreground">{product.price}</p>
              </CardContent>
              <CardFooter className="p-4">
                <Button className="w-full">Add to Cart</Button>
              </CardFooter>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}