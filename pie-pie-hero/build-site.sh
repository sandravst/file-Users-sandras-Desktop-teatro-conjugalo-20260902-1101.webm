#!/usr/bin/env bash
# Builds a standalone web page (site/index.html) from index.html for GitHub Pages.
# The Claude page adds a document head, viewport and a small reset at publish time;
# this script adds the same things so the game works as a normal website.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p site
{
  cat <<'HEAD'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Pie Pie Hero: a 5-level math mystery game. Solve addition, multiplication, fraction, money and subtraction clues to find the missing pie recipe.">
<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
html, body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
HEAD
  # move the page's <title>, meta and <link> tags into <head>, the rest into <body>
  grep -E '^<(title|meta|link)' index.html
  echo '</head>'
  echo '<body>'
  grep -vE '^<(title|meta|link)' index.html
  echo '</body>'
  echo '</html>'
} > site/index.html
touch site/.nojekyll
echo "Built site/index.html"
