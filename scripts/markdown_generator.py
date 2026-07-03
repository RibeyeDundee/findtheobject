class MarkdownGenerator:
    def __init__(self):
        self.lines = []

    def front_matter(self, title='', date='', draft='', expiration_date='', tags=[]):
        if draft == 1:
            draft = 'true'
        else:
            draft = 'false'

        self.lines.append('+++')
        self.lines.append(f'title = \'{title}\'')
        self.lines.append(f'date = {date}')
        self.lines.append(f'draft = {draft}')
        if expiration_date:
            self.lines.append(f'expiryDate = {expiration_date}')
        self.lines.append(f'tags = [')

        for tag in tags.split(' '):
            if tag:
                self.lines.append(f'\'{tag}\',')

        self.lines.append(f']')
        self.lines.append('+++')


    def subtitle(self, subtitle=''):
        if subtitle:
            self.lines.append(subtitle)
        self.lines.append('<!--more-->')

    def difficulty_badge(self, difficulty):
        colors = {
            "hard":"red",
            "impossible":"red",
            "medium":"yellow",
            "easy":"green"
        }

        self.lines.append(f'![Static Badge](https://img.shields.io/badge/{difficulty}-{colors[difficulty]}?style=for-the-badge)')

    def photo(self,alt, path):
        self.lines.append(f'![{alt}]({path})')

    def body(self, header, text):
        if header:
            self.lines.append(f'### {header}')
        if text:
            self.lines.append(text)

    def hints(self, hints):
        if hints:
            self.lines.append('### ❓Hints')
            self.lines.append('{{% details title="👀" closed="true" %}}')
            for hint in hints:
                self.lines.append(f'- {hint[0]}')
            self.lines.append('{{% /details %}}')

    def location(self, post_id):
        self.lines.append('### 🎯 Location')
        self.lines.append('{{% details title="👀" closed="true" %}}')
        self.lines.append('{{% details title="⚠️ Spoilers ahead! Tap/click to continue to the object location ⚠️" closed="true" %}}')
        self.photo(alt='Found', path=f'../images/{post_id}-found.jpg')
        self.lines.append('{{% /details %}}')
        self.lines.append('{{% /details %}}')
    
    def location_message(self):
        self.lines.append('### 🎯 Location')
        self.lines.append('{{% details title="👀" closed="true" %}}')
        self.lines.append('🗓️ The location for this object will be posted tomorrow -- See you then!')
        self.lines.append('{{% /details %}}')

    def clear(self):
        self.lines = []

    def output(self):
        return "\n".join(self.lines)
