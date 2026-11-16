import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ChartErrorBoundaryProps {
  children: ReactNode
  title: string
}

interface ChartErrorBoundaryState {
  hasError: boolean
}

export class ChartErrorBoundary extends Component<
  ChartErrorBoundaryProps,
  ChartErrorBoundaryState
> {
  state: ChartErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ChartErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Dashboard chart failed to load or render', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="border-border/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-base font-semibold">{this.props.title}</CardTitle>
            <CardDescription>Chart unavailable</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              role="alert"
              className="flex h-[280px] items-center justify-center rounded-lg text-sm text-muted-foreground"
            >
              This chart could not be loaded. Reload the page to try again.
            </div>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}
