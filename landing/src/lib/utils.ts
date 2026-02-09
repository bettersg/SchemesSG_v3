import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import SVGPathCommander from "svg-path-commander"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


// Function to convert SVG path `d` to vertices
export function parsePathToVertices(path: string, sampleLength = 15) {
  // Convert path to absolute commands
  const commander = new SVGPathCommander(path)

  const points: { x: number; y: number }[] = []
  let lastPoint: { x: number; y: number } | null = null

  // Get total length of the path
  const totalLength = commander.getTotalLength()
  let length = 0

  // Sample points along the path
  while (length < totalLength) {
    const point = commander.getPointAtLength(length)

    // Only add point if it's different from the last one
    if (!lastPoint || point.x !== lastPoint.x || point.y !== lastPoint.y) {
      points.push({ x: point.x, y: point.y })
      lastPoint = point
    }

    length += sampleLength
  }

  // Ensure we get the last point
  const finalPoint = commander.getPointAtLength(totalLength)
  if (
    lastPoint &&
    (finalPoint.x !== lastPoint.x || finalPoint.y !== lastPoint.y)
  ) {
    points.push({ x: finalPoint.x, y: finalPoint.y })
  }

  return points
}

export function calculatePosition(
  value: number | string | undefined,
  containerSize: number,
  elementSize: number
): number {
  // Handle percentage strings (e.g. "50%")
  if (typeof value === "string" && value.endsWith("%")) {
    const percentage = parseFloat(value) / 100
    return containerSize * percentage
  }

  // Handle direct pixel values
  if (typeof value === "number") {
    return value
  }

  // If no value provided, center the element
  return (containerSize - elementSize) / 2
}