import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Mail, Github, Linkedin } from "lucide-react"
import Image from "next/image"

export default function Component() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="max-w-4xl mx-auto">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="md:w-1/3">
              <Image
                src="/images/hero.jpeg?height=300&width=300"
                alt="Profile Picture"
                width={300}
                height={300}
                className="rounded mx-auto"
              />
            </div>
            <div className="md:w-2/3">
              <h1 className="text-3xl font-bold mb-2">Muhammad Aitazaz Ahsan</h1>
              <h2 className="text-xl text-muted-foreground mb-4">BE Software Engineering</h2>
              <p className="mb-4">
                Brief introduction about yourself. Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
                Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                Im doing Software Engineering from <br />                        
                 Military College of Signals, NUST 
              </p>
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  <Badge>HTML</Badge>
                  <Badge>CSS</Badge>
                  <Badge>C++</Badge>
                  <Badge>JAVA</Badge>
                  <Badge>Next JS</Badge>
                </div>
              </div>
              <div className="flex gap-4">
                <Button variant="outline" size="icon">
                  <Mail className="h-4 w-4" />
                  <span className="sr-only">Email</span>
                </Button>
                <Button variant="outline" size="icon">
                  <Github className="h-4 w-4" />
                  <span className="sr-only">GitHub</span>
                </Button>
                <Button variant="outline" size="icon">
                  <Linkedin className="h-4 w-4" />
                  <span className="sr-only">LinkedIn</span>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}