import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      collapsible: false,
      items: [
        'getting-started',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'cli',
        {
          type: 'category',
          label: 'Runtime',
          items: [
            'runtime/local-runtime',
          ],
        },
        {
          type: 'category',
          label: 'Packaging',
          items: [
            'packaging-agents',
            'installing-agents',
            'inspecting-l6e-packages',
          ],
        },
        {
          type: 'category',
          label: 'Prompting',
          items: [
            'using-prompt-builder',
            'prompt/agent-forge-context-prompt',
          ],
        },
        {
          type: 'category',
          label: 'Memory',
          items: [
            'memory/sdk-overview',
            'memory/vector-search',
            'memory/conversation-history',
            'memory/using-collections',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
