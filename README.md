
# How to host and format a resume using Github pages

## Purpose

The purpose of this resume is to describe the practical steps of how to host and format a resume using Github pages while relating those practical steps to the general principles of current Technical Writing as explained in Andrew Etter's book Modern Technical Writing.

## Prerequisites
The prerequisites needed to host a resume on a Github page include:  
1. A good understanding on formatting in Markdown
2. A resume formatted in markdown
3. A device with internet connection
4. A Github account

## Instructions

Please follow the step-by-step instructions below to successfully host and format a resume on a GitHub page. Most steps will be related to Andrew Etter's book on Modern technical Writing, a link to this book can be found under more resources.

### Creating my Github repository

Andrew Etter highlights the importance of using a Distributed Version Control to host a site in his book and we will be using one of Etter's recommendations which is Github.

1. Log into your Github Account with your username and password.
2. Click the "new" button on the top left part of the screen to begin creating a new repository.
3. Enter "Ownername.github.io" in Repository name field.
4. Select the "public" option to make repository public.
5. Click the "create repository" button at the end of the page.  

RESULT: A new page appears, it is the homepage of your newly created repository.

### Adding my resume to my repository

Your resume should be formatted in markdown which is a lightweight markup language which makes it easier to host your documentation online. Andrew Etter highlights the importance of using a Lightweight markup language to host a site on Github pages in his book and recommends Github Flavoured Markdown as a fine choice for a Markdown "flavour".

1. Click the "uploading an existing file" or "Add file" button in the top half of the new page to upload your markdown formatted resume.
2. Drag and drop your resume to the dialog box or select your resume from your device by clicking "choose your files".
3. Add a comment under "commit changes" to describe what change you made i.e. adding a new file.
4. Click the "Commit changes" button.

RESULT: your resume now appears on the home page of your repository.

### Making sure my resume can be recognized as the main page of my Github pages site

1. Click on the name of your resume on the homepage.
2. Click on the pencil icon at the top right corner of the dialogue box displaying the resume to edit the resume file.
3. Click into the field that displays the name of your resume.
4. Rename it to "index.md" to make it your entry file for your site.
5. Click "commit changes" at the bottom of the screen.

RESULT: Your resume can now be hosted and recognized as the first page to be seen on your site.

### Deploying my Github pages site

1. Click on "settings" at the top of the screen.
2. Click on "Pages" tab on the left side of the screen.
3. Click on the drop down menu immediately below "Source".
4. Select "Deploy from a branch" from the drop down list.
5. Click on the drop down menu immediately below "Branch".
6. Select "main" from the drop down list.
7. Click on the "Save" button on the right side of the drop down menu.
8. Wait for up to 10 minutes for your site to be deployed.

RESULT: Your site has been deployed with your resume as the main page.

### Viewing my Github pages site

![Viewing my Github pages site gif](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOTgwMzY4Zjc1NzI5OWNiMTViMDBmODU2NTNiZjc0NjMxN2ZmNTJiMiZjdD1n/fkSHnzgzJcwYJt4hOM/giphy.gif)

1. Click on "settings" at the top of your repository homepage.
2. Click on "Pages" tab on the left side of the screen.
3. Click "view site" at the top of the page as shown in gif above.

RESULT: A new web-page opens in another tab which displays your hosted resume.

### Formatting my Github pages site using jekyll

Jekyll is a static site generator with built-in support for Github Pages. Jekyll gives you a lot of flexibility to customize how it builds your site. These options can either be specified in a _config.yml or _config.toml file placed in your site’s root directory, or can be specified as flags for the jekyll executable in the terminal. Andrew Etter recommends Jekyll as a tool to create a beautiful, functional documentation website in his book. These steps will guide you on how to apply jekyll configurations to your Github Pages site.

1. Add some formatting by clicking on "add file" on the home page.
2. Select "create a new file" from the drop down list.
3. Enter "_config.yml" as the name of the file.
4. Add the formatting you want to the file, a link to various formatting options is included under more resources.
5. Commit the file after adding your formatting.
6. Wait for up to 10 minutes for your changes to get applied to your resume.

RESULT: Your formatting has been added to your hosted resume page.

### Creating a README file
Andrew Etter recommends creating a "README.md" file in the root of the repository for the purpose of giving a quick summary of what you are hosting, instructions on how to build the documentation locally and instructions on how to contribute to it.

1. Click on "add file" on the home page.
2. Select "create a new file" from the drop down list.
3. Enter "README.md" as the name of the file.
4. Enter the information you would like to be in the readme.
5. Commit the file.

RESULT: Your README.md file contents will be displayed on the homepage of your repository.

### More Resources

1. [MarkDown tutorial](www.github.com)
2. [Andrew Etter's Modern Technical Writing book](https://www.amazon.ca/Modern-Technical-Writing-Introduction-Documentation-ebook/dp/B01A2QL9SS)
3. [How to add a some formatting to your Github page site](https://jekyllrb.com/docs/configuration/)

## Authors and Acknowledgments

* [Readme.so](https://readme.so/editor) was a good template tool for my initial Readme.md creation.
* Thankful for the reviews from my group members Cody, Hong and Rolf.
* Credits to [Aliou/ace](https://github.com/aliou/ace) for the theme used for my resume.

## FAQs
1. "Why is Markdown better than a word
processor?"  
Markdown is a better than a word processor because it is easier to learn how to use, it is also easier to convert Markdown to HTML unlike MS Word. Overall, it is a better and more effective tool for text that will be published online. 

2. "Why is my resume not showing up?"  
Your resume could not show up because your resume is not in the root directory of your repository or your resume is not named properly for it to be recognized. Also your resume could not be showing because your github pages settings is not building from the correct source and branch.
