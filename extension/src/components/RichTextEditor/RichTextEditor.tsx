import React, { useMemo } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import { getExtensions } from './extensions';
import EditorToolbar from './EditorToolbar';

interface RichTextEditorProps {
  content: string;
  onUpdate?: (html: string) => void;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ content, onUpdate }) => {

  // Extract PDF styles (CSS) from the HTML content
  const styles = useMemo(() => {
    const styleTags = content.match(/<style[^>]*>([\s\S]*?)<\/style>/gi);
    if (!styleTags) return '';

    return styleTags.map(tag => {
        const match = tag.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
        return match ? match[1] : '';
    }).join('\n');
  }, [content]);

  const editor = useEditor({
    extensions: getExtensions(),
    content: content,
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
                background: #ccc;
                padding: 0;
                width: fit-content; /* Allow ProseMirror to grow with content */
                min-width: 100%; /* But at least fill the container */
            }
            /* Center the PDF page div and ensure it can grow beyond viewport */
            div[id^="page"] {
                margin: 0 auto !important;
                background: white;
                max-width: none !important; /* Prevent any max-width constraint */
                /* Don't override width - let inline styles from backend work */
            }
            /* Minimal table styles - let backend dynamic styles take precedence */
            .ProseMirror table {
                border-collapse: collapse;
                table-layout: fixed;
                margin: 0;
                /* Remove static width to allow natural sizing */
            }
            .ProseMirror td, .ProseMirror th {
                /* Removed min-width - let backend control column widths via colgroup */
                /* Remove static borders and padding - use inline styles from backend */
                vertical-align: top;
            }
         `}</style>
         <EditorContent editor={editor} className="h-full" />
      </div>
    </div>
  );
};

export default RichTextEditor;
