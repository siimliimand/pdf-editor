import React from 'react';
import { Editor } from '@tiptap/react';
import {
  Bold, Italic, Underline as UnderlineIcon, Link as LinkIcon,
  Table as TableIcon, Plus, Trash2,
  Rows, Columns
} from 'lucide-react';

interface EditorToolbarProps {
  editor: Editor | null;
  onSetLink: () => void;
  onAddTable: () => void;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({ editor, onSetLink, onAddTable }) => {
  if (!editor) {
    return null;
  }

  return (
      <div className="bg-white border-b border-gray-200 p-2 flex flex-wrap gap-2 items-center sticky top-0 z-50 shadow-sm">

        {/* Text Formatting */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
            <button
                onClick={() => editor.chain().focus().toggleBold().run()}
                disabled={!editor.can().chain().focus().toggleBold().run()}
                className={`p-1.5 rounded hover:bg-gray-100 transition-colors ${editor.isActive('bold') ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
                title="Bold"
            >
                <Bold size={18} />
            </button>
            <button
                onClick={() => editor.chain().focus().toggleItalic().run()}
                disabled={!editor.can().chain().focus().toggleItalic().run()}
                className={`p-1.5 rounded hover:bg-gray-100 transition-colors ${editor.isActive('italic') ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
                title="Italic"
            >
                <Italic size={18} />
            </button>
            <button
                onClick={() => editor.chain().focus().toggleUnderline().run()}
                className={`p-1.5 rounded hover:bg-gray-100 transition-colors ${editor.isActive('underline') ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
                title="Underline"
            >
                <UnderlineIcon size={18} />
            </button>
             <button
                onClick={() => editor.chain().focus().unsetAllMarks().run()}
                className="p-1.5 rounded hover:bg-gray-100 transition-colors text-gray-600"
                title="Clear Formatting"
            >
                <Trash2 size={18} />
            </button>
        </div>

        {/* Colors */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
            <div className="flex items-center gap-1 px-1">
                <input
                    type="color"
                    onInput={event => editor.chain().focus().setColor((event.target as HTMLInputElement).value).run()}
                    value={editor.getAttributes('textStyle').color || '#000000'}
                    className="w-6 h-6 p-0 border-0 rounded cursor-pointer"
                    title="Text Color"
                />
            </div>
        </div>

        {/* Links */}
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
            <button
                onClick={onSetLink}
                className={`p-1.5 rounded hover:bg-gray-100 transition-colors ${editor.isActive('link') ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
                title="Link"
            >
                <LinkIcon size={18} />
            </button>
             <button
                onClick={() => editor.chain().focus().unsetLink().run()}
                disabled={!editor.isActive('link')}
                className="p-1.5 rounded hover:bg-gray-100 transition-colors text-gray-600 disabled:opacity-30"
                title="Unlink"
            >
                <div className="font-bold text-xs strike-through">Broken Link</div>
            </button>
        </div>

        {/* Tables */}
        <div className="flex items-center gap-1">
            <button
                onClick={onAddTable}
                className="p-1.5 rounded hover:bg-gray-100 transition-colors text-gray-600"
                title="Insert Table"
                >
                <TableIcon size={18} />
            </button>

            {editor.isActive('table') && (
                <>
                <button
                    onClick={() => editor.chain().focus().addColumnAfter().run()}
                    className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
                    title="Add Column"
                ><Columns size={16} /><Plus size={10} className="-mt-2 -ml-1 inline" /></button>
                <button
                    onClick={() => editor.chain().focus().deleteColumn().run()}
                    className="p-1.5 rounded hover:bg-gray-100 text-red-600"
                    title="Delete Column"
                ><Columns size={16} /><Trash2 size={10} className="-mt-2 -ml-1 inline" /></button>
                <button
                    onClick={() => editor.chain().focus().addRowAfter().run()}
                     className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
                     title="Add Row"
                ><Rows size={16} /><Plus size={10} className="-mt-2 -ml-1 inline" /></button>
                 <button
                    onClick={() => editor.chain().focus().deleteRow().run()}
                     className="p-1.5 rounded hover:bg-gray-100 text-red-600"
                     title="Delete Row"
                ><Rows size={16} /><Trash2 size={10} className="-mt-2 -ml-1 inline" /></button>

                 <button
                    onClick={() => editor.chain().focus().deleteTable().run()}
                     className="p-1.5 rounded hover:bg-gray-100 text-red-600"
                     title="Delete Table"
                ><Trash2 size={18} /></button>
                </>
            )}
        </div>
      </div>
  );
};

export default EditorToolbar;
