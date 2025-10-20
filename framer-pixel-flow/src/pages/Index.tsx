import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useScreenSize } from "@/components/hooks/use-screen-size"
import { HandWrittenTitle } from "@/components/ui/hand-writing-text"
import { HeroHighlight } from "@/components/ui/hero-highlight"

const Index = () => {
  const screenSize = useScreenSize()
  const [isAnimating, setIsAnimating] = useState(false)
  const [clickPosition, setClickPosition] = useState({ x: 0, y: 0 })

  // 计算从点击点到屏幕最远角的距离作为半径
  const calculateRadius = (x: number, y: number) => {
    const screenWidth = window.innerWidth
    const screenHeight = window.innerHeight
    const xDist = Math.max(x, screenWidth - x)
    const yDist = Math.max(y, screenHeight - y)
    return Math.sqrt(xDist ** 2 + yDist ** 2)
  }

  const radius = calculateRadius(clickPosition.x, clickPosition.y)

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // 阻止默认的父级事件，如果需要的话
    e.stopPropagation()
    setClickPosition({ x: e.clientX, y: e.clientY })
    setIsAnimating(true)
  }

  const handleAnimationComplete = () => {
    // 在这里执行页面跳转逻辑
    console.log("动画完成，准备跳转到下一页！")
    // 例如: window.location.href = "/next-page";
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 1 }}
        animate={{ opacity: isAnimating ? 0 : 1 }}
        transition={{ duration: 0.4 }} // 让页面内容在圆形放大前稍微淡出
      >
        <HeroHighlight
          containerClassName="relative w-full h-screen bg-[#dcddd7] text-foreground overflow-hidden"
          className="w-full h-full"
        >
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-start pointer-events-none space-y-2 md:space-y-8">
              <h1 className="text-3xl sm:text-5xl md:text-7xl tracking-tight font-bold tracking-[0.44em]">
                探究·拆解·
                <span className="relative z-0 inline-block after:absolute after:content-[''] after:left-0 after:right-0 after:bottom-[-0.05em] after:h-[0.4em] after:bg-gradient-to-r after:from-[#ffa04f] after:to-amber-300 after:rounded-sm after:-z-10 after:translate-x-[-0.2em]">
                  原理
                </span>
              </h1>
              <p className="text-xs md:text-2xl text-muted-foreground tracking-[0.3em]">
                以直击核心的方式，从原理开始学习
              </p>
            </div>
            {/* ↓↓↓ 在这里添加 onClick 事件 ↓↓↓ */}
            <HandWrittenTitle
              onClick={handleClick}
              titleClassName="text-3xl md:text-3xl bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text bg-no-repeat bg-[length:0%_100%] transition-all duration-300 ease-in-out hover:text-transparent hover:bg-[length:100%_100%]"
              subtitleClassName="bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text bg-no-repeat bg-[length:0%_100%] transition-all duration-300 ease-in-out hover:text-transparent hover:bg-[length:100%_100%]"
              title="现在！开始学习！"
              subtitle="Start Learning Now"
              scale={0.7}
              className="mx-auto relative z-30 mt-32"
            />
          </div>
        </HeroHighlight>
      </motion.div>

      {/* ↓↓↓ 这是我们的圆形扩散动画元素 ↓↓↓ */}
      <AnimatePresence>
        {isAnimating && (
          <motion.div
            className="fixed top-0 left-0 bg-[#dcddd7] z-50" // 使用和背景一致的颜色
            style={{
              width: radius * 2,
              height: radius * 2,
              top: clickPosition.y - radius,
              left: clickPosition.x - radius,
              borderRadius: "50%",
            }}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }} // 如果需要返回动画
            transition={{ duration: 0.5, ease: "easeOut" }}
            onAnimationComplete={handleAnimationComplete}
          />
        )}
      </AnimatePresence>
    </>
  )
}

export default Index