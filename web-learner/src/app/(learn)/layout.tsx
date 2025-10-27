import * as React from 'react';
import LearnLayoutContent from './learn-layout-content';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function LearnLayout({ children }: any) {
  return React.createElement(
    React.Suspense,
    { fallback: <div>Loading Layout...</div> },
    React.createElement(LearnLayoutContent, null, children ?? null),
  );
}
