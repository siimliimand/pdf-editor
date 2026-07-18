import React, { useMemo } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import { getExtensions } from './extensions';
import EditorToolbar from './EditorToolbar';

interface RichTextEditorProps {
  content: string;
  onUpdate?: (html: string) => void;
}

/**
 * Extract the body content from a full HTML document.
 * If the content is a full HTML document (has <html>/<body> tags), extract just the body content.
 * If it's already an HTML fragment, return as-is.
 * Also injects inline width/height on page-container divs.
 */
function extractBodyContent(html: string): string {
  // Extract page dimensions from CSS first
  let pageWidth = 0;
  let pageHeight = 0;
  const widthMatch = html.match(/\.page-container\s*\{[\s\S]*?width:\s*([\d.]+)px/);
  const heightMatch = html.match(/\.page-container\s*\{[\s\S]*?height:\s*([\d.]+)px/);
  if (widthMatch) pageWidth = parseFloat(widthMatch[1]);
  if (heightMatch) pageHeight = parseFloat(heightMatch[1]);

  // Check if this is a full HTML document
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  let bodyContent = bodyMatch ? bodyMatch[1].trim() : html;

  // If no dimensions from CSS, use A4 at 96 DPI as default
  if (pageWidth === 0 || pageHeight === 0) {
    pageWidth = 794;
    pageHeight = 1123;
  }

  // Inject inline dimensions on page-container divs
  if (pageWidth > 0 && pageHeight > 0) {
    bodyContent = bodyContent.replace(
      /(<div\s+class="page-container")/g,
      `$1 style="width: ${pageWidth}px; height: ${pageHeight}px; position: relative; overflow: hidden; background: white;"`
    );
  }

  return bodyContent;
}

/**
 * Extract CSS styles from the HTML content (without dimensions, those go inline).
 */
function extractStyles(html: string) {
  const styleTags = html.match(/<style[^>]*>([\s\S]*?)<\/style>/gi) || [];
  return styleTags.map(tag => {
    const match = tag.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
    return match ? match[1] : '';
  }).join('\n');
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ content, onUpdate }) => {

  // Extract body content and styles from the HTML
  const { bodyContent, styles } = useMemo(() => {
    const bodyContent = extractBodyContent(content);
    const styles = extractStyles(content);
    return { bodyContent, styles };
  }, [content]);

  const editor = useEditor({
    extensions: getExtensions(),
    content: bodyContent,
    onUpdate: ({ editor }) => {
      onUpdate?.(editor.getHTML());
    },
    editorProps: {
        attributes: {
            class: 'w-full focus:outline-none min-h-[500px] bg-white relative', // Removed padding to match PDF layout
            style: 'min-height: 100%;'
        }
    }
  });

  if (!editor) {
    return null;
  }

  const setLink = () => {
    const previousUrl = editor.getAttributes('link').href;
    const url = window.prompt('URL', previousUrl);
    if (url === null) return;
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run();
      return;
    }
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run();
  };

  const addTable = () => {
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-lg overflow-hidden border border-gray-200 shadow-sm relative">
       {/* Inject extracted styles */}
       {styles && (
         <style dangerouslySetInnerHTML={{ __html: styles }} />
       )}

       <EditorToolbar
         editor={editor}
         onSetLink={setLink}
         onAddTable={addTable}
       />

      {/* Editor Area */}
      <div className="flex-grow overflow-auto custom-scrollbar bg-gray-100 p-4" style={{overflowX: 'auto', overflowY: 'auto'}}>
         <style>{`
            .ProseMirror {
                outline: none;
                min-height: 100%;
                background: transparent;
                padding: 0;
                width: fit-content;
                min-width: 100%;
            }
            /* Page container styling - dimensions are now inline */
            .page-container {
                margin: 0 auto !important;
                background: white;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            /* Center the PDF page div and ensure it can grow beyond viewport */
            div[id^="page"] {
                margin: 0 auto !important;
                background: white;
                max-width: none !important;
            }
            /* Minimal table styles - let backend dynamic styles take precedence */
            .ProseMirror table {
                border-collapse: collapse;
                table-layout: fixed;
                margin: 0;
            }
            .ProseMirror td, .ProseMirror th {
                vertical-align: top;
            }
         `}</style>
         <EditorContent editor={editor} className="h-full" />
      </div>
    </div>
  );
};

export default RichTextEditor;
