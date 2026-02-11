"""
OpenSubtitles search results selector window
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OpenSubtitlesSelectorWindow:
    """Window for selecting subtitles from OpenSubtitles search results"""
    
    def __init__(self, parent, search_results, controller):
        """
        Initialize selector window

        Args:
            parent: Parent window
            search_results: List of search results from OpenSubtitles
            controller: Application controller
        """
        self.parent = parent
        self.search_results = search_results
        self.controller = controller
        self.selected_result = None
        self.window = None
        self.results_map = {}  # Map tree item ID to result dict
        
    def show(self):
        """Show the selector window and return selected result"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🌐 Seleziona Sottotitoli - OpenSubtitles")
        self.window.geometry("900x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self._create_ui()
        
        # Wait for window to close
        self.window.wait_window()
        
        return self.selected_result
    
    def _create_ui(self):
        """Create the user interface"""
        # Header
        header_frame = ttk.Frame(self.window, padding="10")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text=f"🎬 Trovati {len(self.search_results)} sottotitoli",
            font=('Arial', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            header_frame,
            text="Seleziona il migliore per il tuo video",
            font=('Arial', 9),
            foreground='gray'
        ).pack(side=tk.LEFT, padx=10)
        
        # Info frame
        info_frame = ttk.Frame(self.window, padding="5")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(
            info_frame,
            text="💡 Suggerimento: Ordina per 'Download' per trovare i più popolari, o per 'Rating' per i migliori",
            font=('Arial', 8, 'italic'),
            foreground='blue'
        ).pack()
        
        # Results list frame
        list_frame = ttk.Frame(self.window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview with columns
        columns = ('language', 'name', 'release', 'downloads', 'rating', 'uploader', 'hearing_impaired')
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', selectmode='browse')
        
        # Define column headings
        self.tree.heading('#0', text='#', anchor=tk.W)
        self.tree.heading('language', text='Lingua', anchor=tk.W)
        self.tree.heading('name', text='Nome File', anchor=tk.W)
        self.tree.heading('release', text='Release', anchor=tk.W)
        self.tree.heading('downloads', text='Download', anchor=tk.CENTER)
        self.tree.heading('rating', text='Rating', anchor=tk.CENTER)
        self.tree.heading('uploader', text='Uploader', anchor=tk.W)
        self.tree.heading('hearing_impaired', text='HI', anchor=tk.CENTER)
        
        # Define column widths
        self.tree.column('#0', width=40, stretch=False)
        self.tree.column('language', width=80, stretch=False)
        self.tree.column('name', width=250, stretch=True)
        self.tree.column('release', width=150, stretch=False)
        self.tree.column('downloads', width=80, stretch=False)
        self.tree.column('rating', width=60, stretch=False)
        self.tree.column('uploader', width=100, stretch=False)
        self.tree.column('hearing_impaired', width=40, stretch=False)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        # Populate tree
        self._populate_tree()
        
        # Bind double-click
        self.tree.bind('<Double-Button-1>', lambda e: self._on_select())
        
        # Details frame
        details_frame = ttk.LabelFrame(self.window, text="Dettagli Sottotitolo Selezionato", padding="10")
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.details_text = tk.Text(details_frame, height=4, wrap=tk.WORD, state='disabled')
        self.details_text.pack(fill=tk.X)
        
        # Bind selection change
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.window, padding="10")
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame,
            text="✅ Seleziona e Scarica",
            command=self._on_select,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="❌ Annulla",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Sort buttons
        ttk.Label(buttons_frame, text="Ordina per:").pack(side=tk.LEFT, padx=(20, 5))
        
        ttk.Button(
            buttons_frame,
            text="⬇️ Download",
            command=lambda: self._sort_by('downloads'),
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame,
            text="⭐ Rating",
            command=lambda: self._sort_by('rating'),
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame,
            text="🔤 Nome",
            command=lambda: self._sort_by('name'),
            width=12
        ).pack(side=tk.LEFT, padx=2)
    
    def _populate_tree(self):
        """Populate tree with search results"""
        for idx, result in enumerate(self.search_results, 1):
            attributes = result.get('attributes', {})

            language = attributes.get('language', 'unknown')
            file_name = attributes.get('files', [{}])[0].get('file_name', 'Unknown')
            release = attributes.get('release', '-')
            downloads = attributes.get('download_count', 0)
            rating = attributes.get('ratings', 0)
            uploader = attributes.get('uploader', {}).get('name', 'Unknown')
            hearing_impaired = '✓' if attributes.get('hearing_impaired', False) else '✗'

            # Format rating
            if rating > 0:
                rating_str = f"⭐ {rating:.1f}"
            else:
                rating_str = "-"

            # Insert into tree with index as tag
            item_id = self.tree.insert(
                '',
                'end',
                text=f"{idx}",
                values=(
                    language,
                    file_name,
                    release,
                    f"{downloads:,}",
                    rating_str,
                    uploader,
                    hearing_impaired
                ),
                tags=(str(idx),)  # Use string index as tag
            )

            # Store result in map (tkinter tags can't store complex objects)
            self.results_map[item_id] = result
    
    def _on_tree_select(self, event):
        """Handle tree selection change"""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]

        # Get result from map using item ID
        if item_id in self.results_map:
            result = self.results_map[item_id]
            self._show_details(result)
    
    def _show_details(self, result):
        """Show details of selected subtitle"""
        try:
            attributes = result.get('attributes', {})
            
            details = []
            details.append(f"📁 Nome File: {attributes.get('files', [{}])[0].get('file_name', 'Unknown')}")
            details.append(f"🌐 Lingua: {attributes.get('language', 'unknown')}")
            details.append(f"📦 Release: {attributes.get('release', '-')}")
            details.append(f"⬇️ Download: {attributes.get('download_count', 0):,}")
            details.append(f"⭐ Rating: {attributes.get('ratings', 0):.1f}/10" if attributes.get('ratings', 0) > 0 else "⭐ Rating: N/A")
            details.append(f"👤 Uploader: {attributes.get('uploader', {}).get('name', 'Unknown')}")
            details.append(f"♿ Hearing Impaired: {'Sì' if attributes.get('hearing_impaired', False) else 'No'}")
            
            # Add comments if available
            if 'comments' in attributes:
                details.append(f"\n💬 Commenti: {attributes['comments'][:100]}...")
            
            details_text = "\n".join(details)
            
            self.details_text.config(state='normal')
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details_text)
            self.details_text.config(state='disabled')
            
        except Exception as e:
            logger.error(f"Error showing details: {str(e)}")
    
    def _sort_by(self, column):
        """Sort results by column"""
        try:
            # Get all items
            items = [(self.tree.item(item, 'values'), item, self.tree.item(item, 'tags')) 
                     for item in self.tree.get_children()]
            
            # Determine sort key based on column
            if column == 'downloads':
                # Sort by downloads (numeric)
                items.sort(key=lambda x: int(x[0][3].replace(',', '')), reverse=True)
            elif column == 'rating':
                # Sort by rating (numeric)
                def get_rating(values):
                    rating_str = values[4]
                    if rating_str == '-':
                        return -1
                    try:
                        return float(rating_str.split()[1])
                    except:
                        return -1
                items.sort(key=lambda x: get_rating(x[0]), reverse=True)
            elif column == 'name':
                # Sort by name (alphabetic)
                items.sort(key=lambda x: x[0][1].lower())
            
            # Reinsert items in sorted order
            for index, (values, item, tags) in enumerate(items):
                self.tree.move(item, '', index)
            
            logger.info(f"Sorted by {column}")
            
        except Exception as e:
            logger.error(f"Error sorting: {str(e)}")
    
    def _on_select(self):
        """Handle select button click"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un sottotitolo dalla lista!")
            return

        item_id = selection[0]

        # Get result from map
        if item_id in self.results_map:
            self.selected_result = self.results_map[item_id]
            self.window.destroy()
        else:
            messagebox.showerror("Errore", "Impossibile recuperare il risultato selezionato")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.selected_result = None
        self.window.destroy()
