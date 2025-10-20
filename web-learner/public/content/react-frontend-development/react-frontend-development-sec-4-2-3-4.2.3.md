好的，我们已经深入理解了“状态提升”的理论和其背后的数据流模型。理论学习过后，最佳的消化方式莫过于亲手实践。

现在，我们将整合前一节的知识点，将所有碎片拼合起来，从头构建一个功能完整且结构优良的温度转换器，并在这个过程中进一步体会状态提升带来的优雅结构。

***

### 4.2.3 案例实践：构建一个同步的温度转换器

在这一节，我们将一步步地编写代码，最终实现我们的目标应用。我们不仅会构建核心的转换功能，还会通过添加一个额外的小功能来展示“单一数据源”模式的强大扩展性。

#### Case Study: 完整实现与增强

我们将从一个更优化的角度来组织代码，引入一些在实际开发中常用的技巧，比如创建可复用的组件。

**第一步：创建可复用的 `TemperatureInput` 组件**

观察 4.2.2 节中重构后的 `CelsiusInput` 和 `FahrenheitInput`，你会发现它们的结构几乎完全相同，唯一的区别在于 `legend` 标签里的文本。这是代码重复的典型信号。在 React 中，我们应该遵循 DRY (Don't Repeat Yourself) 原则。

因此，一个更好的做法是创建一个通用的 `TemperatureInput` 组件，通过 props 来区分它是用于摄氏度还是华氏度。

```jsx
// TemperatureInput.js
import React from 'react';

// 定义一个映射，方便根据温标名称获取显示文本
const scaleNames = {
  c: '摄氏度 (Celsius)',
  f: '华氏度 (Fahrenheit)'
};

function TemperatureInput(props) {
  const handleChange = (e) => {
    // 调用从父组件传入的回调函数
    props.onTemperatureChange(e.target.value);
  };

  const temperature = props.temperature;
  const scale = props.scale;
  
  return (
    <fieldset>
      <legend>输入{scaleNames[scale]}:</legend>
      {/* value 完全由 props 控制 */}
      <input value={temperature} onChange={handleChange} />
    </fieldset>
  );
}

export default TemperatureInput;
```
这个组件变得更加通用和“笨拙”，它只负责两件事：根据 props 渲染 UI，以及在用户输入时通知父组件。这正是理想的展示组件。

**第二步：添加一个简单的“状态衍生”组件**

为了展示“单一数据源”的威力，我们来增加一个新需求：当温度达到或超过100摄氏度时，显示一条“水会烧开”的提示。

我们可以创建一个非常简单的组件 `BoilingVerdict` 来实现这个逻辑。

```jsx
// BoilingVerdict.js
import React from 'react';

function BoilingVerdict(props) {
  if (props.celsius >= 100) {
    return <p style={{ color: 'red' }}>水会烧开 (The water would boil).</p>;
  }
  return <p>水不会烧开 (The water would not boil).</p>;
}

export default BoilingVerdict;
```
请注意，这个组件本身是无状态的。它接收一个 `celsius` prop，并根据其值渲染不同的结果。它的所有信息都派生自外部传入的数据。

**第三步：组装最终的父组件 `TemperatureConverterApp`**

现在，我们拥有了所有积木块。让我们来搭建核心的父组件，它将负责：
1.  维护唯一的 `temperature` 和 `scale` 状态。
2.  提供处理状态更新的函数。
3.  执行温度转换计算。
4.  将计算后的 props 传递给所有的子组件。

#### Code Example: 完整的应用代码

下面是整个应用聚合在一起的完整、可运行的代码。你可以将其放入一个文件中直接运行查看效果。

```jsx
import React, { useState } from 'react';

// --- 工具函数 ---
function toCelsius(fahrenheit) {
  return ((fahrenheit - 32) * 5) / 9;
}

function toFahrenheit(celsius) {
  return (celsius * 9) / 5 + 32;
}

function tryConvert(temperature, convert) {
  const input = parseFloat(temperature);
  if (Number.isNaN(input)) {
    return '';
  }
  const output = convert(input);
  const rounded = Math.round(output * 1000) / 1000;
  return rounded.toString();
}


// --- 子组件1: BoilingVerdict ---
function BoilingVerdict(props) {
  if (props.celsius >= 100) {
    return <p style={{ color: 'red' }}>水会烧开 (The water would boil).</p>;
  }
  return <p>水不会烧开 (The water would not boil).</p>;
}


// --- 子组件2: TemperatureInput (可复用) ---
const scaleNames = {
  c: '摄氏度 (Celsius)',
  f: '华氏度 (Fahrenheit)'
};

function TemperatureInput(props) {
  const handleChange = (e) => {
    props.onTemperatureChange(e.target.value);
  };

  return (
    <fieldset>
      <legend>输入{scaleNames[props.scale]}:</legend>
      <input value={props.temperature} onChange={handleChange} />
    </fieldset>
  );
}


// --- 父组件: TemperatureConverterApp ---
function TemperatureConverterApp() {
  const [temperature, setTemperature] = useState('');
  const [scale, setScale] = useState('c');

  const handleCelsiusChange = (temperature) => {
    setScale('c');
    setTemperature(temperature);
  };

  const handleFahrenheitChange = (temperature) => {
    setScale('f');
    setTemperature(temperature);
  };
  
  // 基于单一数据源（temperature 和 scale），计算出两个输入框应显示的值
  const celsius = scale === 'f' ? tryConvert(temperature, toCelsius) : temperature;
  const fahrenheit = scale === 'c' ? tryConvert(temperature, toFahrenheit) : temperature;

  return (
    <div>
      {/* 使用可复用组件，并传入各自的 props */}
      <TemperatureInput
        scale="c"
        temperature={celsius}
        onTemperatureChange={handleCelsiusChange}
      />
      <TemperatureInput
        scale="f"
        temperature={fahrenheit}
        onTemperatureChange={handleFahrenheitChange}
      />
      {/* 将衍生状态传递给 BoilingVerdict 组件 */}
      <BoilingVerdict celsius={parseFloat(celsius)} />
    </div>
  );
}

export default TemperatureConverterApp;
```

#### 数据流追踪

让我们再来追踪一次完整的交互流程，以加深理解。假设用户在**摄氏度输入框**中输入了 `100`。
1.  **事件触发**：`TemperatureInput (scale="c")` 的 `onChange` 事件被触发。
2.  **事件上传**：`handleChange` 函数被调用，它执行 `props.onTemperatureChange('100')`。这个 `props.onTemperatureChange` 实际上是父组件传入的 `handleCelsiusChange` 函数。
3.  **状态更新**：`TemperatureConverterApp` 中的 `handleCelsiusChange('100')` 被执行。它调用 `setScale('c')` 和 `setTemperature('100')`。React 安排了一次组件更新。
4.  **父组件重渲染**：`TemperatureConverterApp` 函数重新执行。
    *   `useState` 返回最新的状态：`temperature` 为 `'100'`，`scale` 为 `'c'`。
    *   `celsius` 变量被计算：因为 `scale` 是 `'c'`，所以 `celsius` 直接等于 `temperature`，即 `'100'`。
    *   `fahrenheit` 变量被计算：`tryConvert('100', toFahrenheit)` 被调用，结果为 `'212'`。
5.  **数据下传**：
    *   第一个 `TemperatureInput` (摄氏度) 接收到 `temperature='100'`。
    *   第二个 `TemperatureInput` (华氏度) 接收到 `temperature='212'`。
    *   `BoilingVerdict` 组件接收到 `celsius={100}` (经过 `parseFloat` 转换)。
6.  **子组件重渲染**：
    *   两个输入框根据新的 `temperature` prop 更新其显示的值。
    *   `BoilingVerdict` 组件根据 `celsius` prop 的值，渲染出“水会烧开”的红色提示。

整个应用界面因此保持了完全的同步和一致性。更重要的是，当我们想添加 `BoilingVerdict` 这个新功能时，我们无需修改任何一个 `TemperatureInput` 子组件。我们只需要在父组件中利用已有的、可信的 `celsius` 状态，并将其传递给新的子组件即可。这就是良好架构的魅力。

---

#### 本节小结

通过这个完整的实践案例，我们巩固了“状态提升”模式的应用：
*   **识别并提升**：将共享状态（温度值和单位）提升到共同的父组件 `TemperatureConverterApp` 中。
*   **受控组件**：子组件 `TemperatureInput` 完全由 props 驱动，自身无状态，成为可复用的“受控组件”。
*   **单一数据源**：父组件中的 state 成为整个 UI 的唯一可信来源。所有显示的数据（两个输入框的值、`BoilingVerdict` 的判断）都由这个源头派生而来。
*   **清晰的数据流**：数据通过 props 自上而下流动，更新请求通过回调函数自下而上传递，流程清晰可预测，易于调试。
*   **代码复用与扩展**：良好的状态管理结构使得组件复用（`TemperatureInput`）和功能扩展（添加 `BoilingVerdict`）变得非常简单和自然。