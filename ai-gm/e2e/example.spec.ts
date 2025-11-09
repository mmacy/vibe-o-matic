import { test, expect } from '@playwright/test'

test.describe('AI Game Master', () => {
  test('should display homepage', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('h1')).toContainText('AI Game Master')
    await expect(page.locator('h2')).toContainText('Welcome')
  })

  test('should have setup section', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByText('OpenAI API key')).toBeVisible()
    await expect(page.getByText('Rules PDF')).toBeVisible()
    await expect(page.getByText('Module PDF')).toBeVisible()
  })

  test('should open settings drawer', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('button', { name: 'Settings' }).click()

    await expect(page.getByText('Homebrew rules')).toBeVisible()
    await expect(page.getByText('Ability scores 4d6l')).toBeVisible()
  })

  test('should open journal drawer', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('button', { name: 'Journal' }).click()

    await expect(page.getByText('Journal', { exact: true })).toBeVisible()
  })

  test('should disable start button without required inputs', async ({ page }) => {
    await page.goto('/')

    const startButton = page.getByRole('button', { name: 'Start session' })
    await expect(startButton).toBeDisabled()
  })

  test('should open API key modal', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('button', { name: 'Enter API key' }).click()

    await expect(page.getByText('Enter OpenAI API key')).toBeVisible()
  })
})
