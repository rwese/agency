/**
 * Notes App E2E Tests
 * 
 * Test cases from SPEC.md:
 * TC01 - Create note: New note appears in list
 * TC02 - Edit note: Changes persist after reload
 * TC03 - Delete note: Note removed from list
 * TC04 - Search: Filtered results shown
 * TC05 - Sort by date: Notes ordered correctly
 * TC06 - Dark mode: Theme toggles correctly
 * TC07 - Export JSON: Valid JSON downloaded
 * TC08 - Import JSON: Notes loaded correctly
 * TC09 - Responsive: Works on mobile viewport
 * TC10 - Persistence: Data survives page reload
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

test.describe('Notes App', () => {
  // Setup - clear localStorage before each test
  test.beforeEach(async ({ page }) => {
    await page.goto(`file://${path.resolve(__dirname, '../index.html')}`);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  });

  // TC01 - Create note
  test('TC01: Create note - New note appears in list', async ({ page }) => {
    // Click new note button
    await page.click('#btn-new-note');
    
    // Fill in title and content
    await page.fill('#note-title', 'Test Note');
    await page.fill('#note-content', 'This is a test note');
    
    // Save note
    await page.click('#btn-save');
    
    // Verify note appears in list
    const noteItem = page.locator('.note-item').first();
    await expect(noteItem).toBeVisible();
    await expect(noteItem.locator('.note-item-title')).toContainText('Test Note');
  });

  // TC02 - Edit note
  test('TC02: Edit note - Changes persist after reload', async ({ page }) => {
    // Create a note
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Original Title');
    await page.fill('#note-content', 'Original content');
    await page.click('#btn-save');
    
    // Click on the note in the list
    await page.click('.note-item');
    
    // Edit the note
    await page.fill('#note-title', 'Updated Title');
    await page.fill('#note-content', 'Updated content');
    await page.click('#btn-save');
    
    // Reload page
    await page.reload();
    
    // Verify changes persist
    await page.click('.note-item');
    await expect(page.locator('#note-title')).toHaveValue('Updated Title');
    await expect(page.locator('#note-content')).toHaveValue('Updated content');
  });

  // TC03 - Delete note
  test('TC03: Delete note - Note removed from list', async ({ page }) => {
    // Create a note
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Note to Delete');
    await page.fill('#note-content', 'Will be deleted');
    await page.click('#btn-save');
    
    // Verify note exists
    await expect(page.locator('.note-item')).toHaveCount(1);
    
    // Set up dialog handler before clicking delete
    page.on('dialog', dialog => dialog.accept());
    
    // Delete the note
    await page.click('#btn-delete');
    
    // Verify note is removed
    await expect(page.locator('.note-item')).toHaveCount(0);
    await expect(page.locator('#editor-empty')).toBeVisible();
  });

  // TC04 - Search
  test('TC04: Search - Filtered results shown', async ({ page }) => {
    // Create multiple notes
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Apple Note');
    await page.fill('#note-content', 'About apples');
    await page.click('#btn-save');
    
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Banana Note');
    await page.fill('#note-content', 'About bananas');
    await page.click('#btn-save');
    
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Cherry Note');
    await page.fill('#note-content', 'About cherries');
    await page.click('#btn-save');
    
    // Search for "apple"
    await page.fill('#search-input', 'apple');
    await page.waitForTimeout(300); // Wait for debounce
    
    // Verify only Apple note is shown
    await expect(page.locator('.note-item')).toHaveCount(1);
    await expect(page.locator('.note-item-title').first()).toContainText('Apple');
    
    // Search in content
    await page.fill('#search-input', 'bananas');
    await page.waitForTimeout(300);
    await expect(page.locator('.note-item')).toHaveCount(1);
    await expect(page.locator('.note-item-title').first()).toContainText('Banana');
    
    // Clear search
    await page.fill('#search-input', '');
    await page.waitForTimeout(300);
    await expect(page.locator('.note-item')).toHaveCount(3);
  });

  // TC05 - Sort by date
  test('TC05: Sort by date - Notes ordered correctly', async ({ page }) => {
    // Create notes with timestamps
    // Note 1
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'First Note');
    await page.click('#btn-save');
    await page.waitForTimeout(100);
    
    // Note 2
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Second Note');
    await page.click('#btn-save');
    await page.waitForTimeout(100);
    
    // Note 3
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Third Note');
    await page.click('#btn-save');
    
    // Verify notes are sorted by modified date (descending - newest first)
    const notes = page.locator('.note-item .note-item-title');
    await expect(notes.nth(0)).toContainText('Third Note');
    await expect(notes.nth(1)).toContainText('Second Note');
    await expect(notes.nth(2)).toContainText('First Note');
  });

  // TC06 - Dark mode
  test('TC06: Dark mode - Theme toggles correctly', async ({ page }) => {
    // Check initial state (light theme)
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', 'dark');
    
    // Toggle to dark mode
    await page.click('#btn-toggle-theme');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('#icon-moon')).toBeVisible();
    
    // Toggle back to light mode
    await page.click('#btn-toggle-theme');
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('#icon-sun')).toBeVisible();
    
    // Verify theme persists after reload
    await page.reload();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', 'dark');
  });

  // TC07 - Export JSON
  test('TC07: Export JSON - Valid JSON downloaded', async ({ page }) => {
    // Create some notes
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Export Test');
    await page.fill('#note-content', 'Testing export');
    await page.click('#btn-save');
    
    // Set up download handler
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('#btn-export')
    ]);
    
    // Verify download
    const fileName = download.suggestedFilename();
    expect(fileName).toMatch(/notes-export-\d{4}-\d{2}-\d{2}\.json/);
    
    // Read and validate JSON
    const path = await download.path();
    const content = fs.readFileSync(path, 'utf-8');
    const data = JSON.parse(content);
    
    expect(data.version).toBe('1.0');
    expect(data.exportedAt).toBeDefined();
    expect(data.noteCount).toBe(1);
    expect(data.notes).toHaveLength(1);
    expect(data.notes[0].title).toBe('Export Test');
  });

  // TC08 - Import JSON
  test('TC08: Import JSON - Notes loaded correctly', async ({ page }) => {
    // Create a test JSON file (array format as expected by importNotes)
    const testData = [
      { id: 'note-import-1', title: 'Imported Note 1', content: 'Content 1', createdAt: '2024-01-01T00:00:00.000Z', modifiedAt: '2024-01-01T00:00:00.000Z' },
      { id: 'note-import-2', title: 'Imported Note 2', content: 'Content 2', createdAt: '2024-01-02T00:00:00.000Z', modifiedAt: '2024-01-02T00:00:00.000Z' }
    ];
    
    const testFilePath = path.resolve(__dirname, 'test-import.json');
    fs.writeFileSync(testFilePath, JSON.stringify(testData));
    
    // Set up dialog handlers
    page.on('dialog', dialog => {
      if (dialog.message().includes('existing')) {
        dialog.accept(); // Merge
      }
    });
    
    // Upload file
    const fileInput = page.locator('#file-import');
    await fileInput.setInputFiles(testFilePath);
    
    // Wait for dialog and accept it
    page.once('dialog', dialog => dialog.accept());
    
    // Verify notes are imported (wait for the import to complete)
    await expect(page.locator('.note-item')).toHaveCount(2, { timeout: 10000 });
    
    // Clean up
    fs.unlinkSync(testFilePath);
  });

  // TC09 - Responsive
  test('TC09: Responsive - Works on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify elements are visible and properly sized
    await expect(page.locator('.header')).toBeVisible();
    await expect(page.locator('#btn-new-note')).toBeVisible();
    await expect(page.locator('#search-input')).toBeVisible();
    
    // Verify sidebar is collapsed on mobile
    const sidebar = page.locator('#sidebar');
    const notesList = page.locator('#notes-list');
    await expect(sidebar).toBeVisible();
    
    // Toggle sidebar menu
    await page.click('#sidebar-menu-toggle');
    await expect(notesList).toHaveClass(/expanded/);
    
    // Verify editor is full width
    const editor = page.locator('.editor');
    await expect(editor).toBeVisible();
    
    // Create a note on mobile
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Mobile Test');
    await page.fill('#note-content', 'Testing on mobile');
    await page.click('#btn-save');
    
    await expect(page.locator('.note-item')).toHaveCount(1);
  });

  // TC10 - Persistence
  test('TC10: Persistence - Data survives page reload', async ({ page }) => {
    // Create multiple notes
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Persistent Note 1');
    await page.fill('#note-content', 'Content 1');
    await page.click('#btn-save');
    
    await page.click('#btn-new-note');
    await page.fill('#note-title', 'Persistent Note 2');
    await page.fill('#note-content', 'Content 2');
    await page.click('#btn-save');
    
    // Verify notes exist
    await expect(page.locator('.note-item')).toHaveCount(2);
    
    // Reload the page
    await page.reload();
    
    // Verify notes still exist
    await expect(page.locator('.note-item')).toHaveCount(2);
    
    // Verify theme preference persists
    await page.click('#btn-toggle-theme');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    // Toggle back to light
    await page.click('#btn-toggle-theme');
    await page.reload();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', 'dark');
  });
});
