// Test code samples for Learn Linker (JS)
// Select a snippet and run "快速解释选中代码" to test AST features & platform links.

// ===== 1) Array methods: map / filter / reduce =====
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const evens = doubled.filter(n => n % 2 === 0);
const sum = evens.reduce((acc, n) => acc + n, 0);
console.log('sum of even doubled numbers =', sum);

// ===== 2) Promise & async/await with try-catch + fetch =====
async function loadUsers() {
  try {
    const resp = await fetch('https://jsonplaceholder.typicode.com/users');
    if (!resp.ok) throw new Error('Network error');
    const data = await resp.json();
    console.log('users:', data.map(u => u.name));
  } catch (err) {
    console.error('loadUsers failed:', err);
  }
}
loadUsers();

// ===== 3) Promise.all / race =====
function delay(ms, value) {
  return new Promise(resolve => setTimeout(() => resolve(value), ms));
}
Promise.all([delay(100, 'A'), delay(50, 'B')]).then(values => console.log('all:', values));
Promise.race([delay(100, 'C'), delay(50, 'D')]).then(v => console.log('race:', v));

// ===== 4) DOM: addEventListener (illustrative; run in browser) =====
// document.getElementById('btn')?.addEventListener('click', (e) => {
//   console.log('clicked', e.target);
// });

// ===== 5) Class / extends / super =====
class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a noise.`; }
}
class Dog extends Animal {
  speak() { return `${super.speak()} Woof!`; }
}
const d = new Dog('Rex');
console.log(d.speak());

// ===== 6) Destructuring & spread =====
const user = { id: 1, name: 'Alice', age: 25 };
const { name, ...rest } = user;
const moreAges = [30, 35];
const ages = [20, 25, ...moreAges];
console.log(name, rest, ages);

// ===== 7) for / for-of / conditional / switch =====
for (let i = 0; i < 3; i++) {
  if (i === 1) {
    console.log('i is one');
  } else {
    console.log('i != one');
  }
}
for (const c of ['x', 'y']) {
  switch (c) {
    case 'x': console.log('X'); break;
    default: console.log('other');
  }
}

// ===== 8) import / export (module syntax; for parsing only) =====
// import { readFile } from 'node:fs/promises';
// export function hello(name) { return `Hello, ${name}`; }

// ===== 9) try-catch-finally =====
try {
  JSON.parse('{ invalid }');
} catch (e) {
  console.warn('parse error');
} finally {
  console.log('done');
}

// ===== 10) Set / Map / Symbol (modern syntax hints) =====
const seen = new Set([1, 2, 2, 3]);
const dict = new Map([['a', 1], ['b', 2]]);
const sym = Symbol('k');
console.log(seen.size, dict.get('a'), typeof sym);
