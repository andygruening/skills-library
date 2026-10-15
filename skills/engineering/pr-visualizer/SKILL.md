---
name: pr-visualizer
description: Visualize a GitHub pull request as a self-contained arch.html slide deck, run inside the repository with a PR number. Reads the PR, its linked issue and every changed file, groups the changes into topics with one outcome-focused slide each and expandable technical evidence, then opens the file in the browser. The HTML template lives at assets/team-demo/template.html. Use when the user asks to visualize, demo, present, or explain what a pull request changed and why.
argument-hint: "<pr number>"
---

Check the PR #<pr number> and use the visuals and html tempalte of the team-demo skill to build a demo of what has changed in that PR and why. Go through all changed files and the issue content. Build topics that those changes cover and build one slide for each topic. Include expandable technical evidence for each topic. Spelling should be less technical and outcome driven. Serve the generated html file to my external browser once you are done.
