import { Node, Mark, mergeAttributes } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import { Table } from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import Image from '@tiptap/extension-image';

// Custom Div extension to preserve PDF layout structure
export const Div = Node.create({
  name: 'div',
  group: 'block',
  content: 'block*',
  defining: true,

  parseHTML() {
    return [{ tag: 'div' }];
  },

  renderHTML({ HTMLAttributes }) {
    // Put HTMLAttributes last so they override options.HTMLAttributes
    // This ensures inline styles from the parsed HTML are preserved
    return ['div', mergeAttributes(HTMLAttributes), 0];
  },

  addAttributes() {
    return {
      class: {
        default: null,
        parseHTML: element => element.getAttribute('class'),
        renderHTML: attributes => {
          if (!attributes.class) return {};
          return { class: attributes.class };
        },
      },
      style: {
        default: null,
        parseHTML: element => element.getAttribute('style'),
        renderHTML: attributes => {
          if (!attributes.style) return {};
          return { style: attributes.style };
        },
      },
      id: {
        default: null,
        parseHTML: element => element.getAttribute('id'),
        renderHTML: attributes => {
          if (!attributes.id) return {};
          return { id: attributes.id };
        },
      }
    };
  },
});

// Extension to preserve Spans with classes/styles (crucial for PDF fonts/colors)
export const Span = Mark.create({
  name: 'span',
  priority: 1000,
  parseHTML() {
    return [
      { tag: 'span' },
    ];
  },
  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0];
  },
  addAttributes() {
    return {
      class: {
        default: null,
        parseHTML: element => element.getAttribute('class'),
      },
      style: {
        default: null,
        parseHTML: element => element.getAttribute('style'),
      },
    };
  },
});

// Extension to allow classes/styles on Paragraphs
export const ExtendedParagraph = Node.create({
    name: 'paragraph',
    priority: 1000,
    group: 'block',
    content: 'inline*',
    parseHTML() { return [{ tag: 'p' }] },
    renderHTML({ HTMLAttributes }) { return ['p', HTMLAttributes, 0] },
    addAttributes() {
        return {
            class: { default: null, parseHTML: el => el.getAttribute('class') },
            style: { default: null, parseHTML: el => el.getAttribute('style') },
        }
    }
});

export const getExtensions = () => [
  StarterKit.configure({
    // Disable default paragraph to use our extended one
    paragraph: false,
    heading: false,
  }),
  Div,
  Span,
  ExtendedParagraph,
  Image.extend({
    addAttributes() {
      return {
        ...this.parent?.(),
        style: {
          default: null,
          parseHTML: element => element.getAttribute('style'),
        },
        class: {
          default: 'max-w-full h-auto',
          parseHTML: element => element.getAttribute('class'),
        }
      }
    }
  }).configure({
    inline: true,
    allowBase64: true,
  }),
  Underline,
  Link.configure({
    openOnClick: false,
    HTMLAttributes: {
        class: 'text-blue-500 hover:underline cursor-pointer',
    }
  }),
  Table.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            style: {
                default: null,
                parseHTML: element => element.getAttribute('style'),
            },
            'data-col-widths': {
                default: null,
                parseHTML: element => {
                    // Check for explicit data attribute first (robust definition from backend)
                    const dataAttr = element.getAttribute('data-col-widths');
                    if (dataAttr) return dataAttr;

                    // Extract column widths from colgroup when parsing HTML
                    const colgroup = element.querySelector('colgroup');
                    if (colgroup) {
                        const cols = Array.from(colgroup.querySelectorAll('col'));
                        const widths = cols.map(col => col.getAttribute('style') || '');
                        return JSON.stringify(widths);
                    }
                    return null;
                },
                renderHTML: (attributes) => {
                    // Ensure the data attribute is rendered to the DOM so it persists
                    return {
                        'data-col-widths': attributes['data-col-widths'],
                    };
                }
            }
        }
    },
    renderHTML({ HTMLAttributes }) {
        // Extract stored column widths
        const colWidthsJson = HTMLAttributes['data-col-widths'];
        let colgroupElement: any = null;
        
        if (colWidthsJson) {
            try {
                const widths = JSON.parse(colWidthsJson);
                const cols = widths.map((style: string) => ['col', { style }]);
                colgroupElement = ['colgroup', {}, ...cols];
            } catch (e) {
                console.warn('Failed to parse column widths:', e);
            }
        }
        
        // Keep data attributes in rendered HTML
        // This ensures that the original widths info persists in the DOM
        
        // Build table structure with colgroup if available
        const children = colgroupElement ? [colgroupElement, ['tbody', 0]] : [['tbody', 0]];
        
        return ['table', mergeAttributes(HTMLAttributes), ...children];
    }
  }).configure({
    // Disabled resizable - it adds min-width constraints and strips backend's width property
    resizable: false,
    // Set cellMinWidth to 0 to prevent TipTap from overriding column widths
    cellMinWidth: 0,
    HTMLAttributes: {
      // Removed w-full and table-auto - let backend inline styles control width and layout
      class: 'my-4',
    },
  }),
  TableRow.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            style: {
                default: null,
                parseHTML: element => element.getAttribute('style'),
            }
        }
    }
  }),
  TableHeader.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            style: {
                default: null,
                parseHTML: element => element.getAttribute('style'),
            }
        }
    }
  }).configure({
    HTMLAttributes: {
      class: '',
    },
  }),
  TableCell.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            style: {
                default: null,
                parseHTML: element => element.getAttribute('style'),
            }
        }
    },
    content: 'inline*',
  }).configure({
    HTMLAttributes: {
      class: '',
    },
  }),
  TextStyle,
  Color,
];
