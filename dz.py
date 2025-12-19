import sys
import re
import argparse
from typing import List, Optional, Any, Union

class ConfigParser:
    def __init__(self):
        self.constants = {}
        self.pos = 0
        self.text = ""
        self.line_num = 1
        self.char_pos = 1
        
    def error(self, message: str):
        raise SyntaxError(f"Line {self.line_num}, position {self.char_pos}: {message}")
    
    def skip_whitespace(self):
        while self.pos < len(self.text):
            # Skip single-line comments
            if self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "//":
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.advance()
                continue
            
            # Skip multi-line comments
            if self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "{-":
                self.pos += 2
                self.char_pos += 2
                depth = 1
                while self.pos < len(self.text) and depth > 0:
                    if self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "{-":
                        depth += 1
                        self.pos += 1
                        self.char_pos += 1
                    elif self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "-}":
                        depth -= 1
                        self.pos += 1
                        self.char_pos += 1
                    elif self.text[self.pos] == '\n':
                        self.line_num += 1
                        self.char_pos = 1
                    self.pos += 1
                    self.char_pos += 1
                continue
            
            if not self.text[self.pos].isspace():
                break
            if self.text[self.pos] == '\n':
                self.line_num += 1
                self.char_pos = 1
            else:
                self.char_pos += 1
            self.pos += 1
    
    def advance(self):
        if self.pos >= len(self.text):
            return ''
        if self.text[self.pos] == '\n':
            self.line_num += 1
            self.char_pos = 1
        else:
            self.char_pos += 1
        char = self.text[self.pos]
        self.pos += 1
        return char
    
    def peek(self):
        if self.pos >= len(self.text):
            return ''
        return self.text[self.pos]
    
    def parse_number(self):
        start_pos = self.pos
        number_str = ""
        
        if self.peek() == '-':
            number_str += self.advance()
        
        found_digit = False
        
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            number_str += self.advance()
            found_digit = True
        
        if self.peek() == '.':
            number_str += self.advance()
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                number_str += self.advance()
                found_digit = True
        
        if self.peek() in ('e', 'E'):
            number_str += self.advance()
            if self.peek() in ('+', '-'):
                number_str += self.advance()
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                number_str += self.advance()
        
        if not found_digit:
            self.error("Expected number")
        
        self.char_pos += len(number_str) - (self.pos - start_pos)
        
        if '.' in number_str or 'e' in number_str.lower():
            return float(number_str)
        return int(number_str)
    
    def parse_string(self):
        if self.peek() != "'":
            self.error("Expected string")
        
        self.advance()
        result = []
        
        while self.pos < len(self.text) and self.text[self.pos] != "'":
            if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):
                self.advance()
                if self.text[self.pos] == 'n':
                    result.append('\n')
                elif self.text[self.pos] == 't':
                    result.append('\t')
                elif self.text[self.pos] == '\\':
                    result.append('\\')
                elif self.text[self.pos] == "'":
                    result.append("'")
                else:
                    result.append(self.text[self.pos])
            else:
                result.append(self.text[self.pos])
            self.advance()
        
        if self.pos >= len(self.text):
            self.error("Unclosed string")
        
        self.advance()
        return ''.join(result)
    
    def parse_array(self):
        if self.peek() != '(':
            self.error("Expected array")
        
        self.advance()
        self.skip_whitespace()
        
        values = []
        if self.peek() != ')':
            while True:
                values.append(self.parse_value())
                self.skip_whitespace()
                
                if self.peek() == ')':
                    break
                elif self.peek() == ',':
                    self.advance()
                    self.skip_whitespace()
                else:
                    self.error("Expected ',' or ')' in array")
        
        self.advance()
        return values
    
    def parse_name(self):
        name = []
        while self.pos < len(self.text) and re.match(r'[_a-zA-Z]', self.peek()):
            name.append(self.advance())
        
        if not name:
            self.error("Expected name")
        
        return ''.join(name)
    
    def parse_constant_expression(self):
        if self.peek() != '$':
            self.error("Expected constant expression")
        
        self.advance()
        
        if self.peek() != '[':
            self.error("Expected '[' after '$'")
        self.advance()
        
        self.skip_whitespace()
        
        operation = self.parse_name()
        self.skip_whitespace()
        
        args = []
        while self.peek() != ']':
            args.append(self.parse_value())
            self.skip_whitespace()
        
        self.advance()
        
        if operation == "+":
            if len(args) != 2:
                self.error("'+' requires 2 arguments")
            return self.evaluate(args[0]) + self.evaluate(args[1])
        elif operation == "-":
            if len(args) != 2:
                self.error("'-' requires 2 arguments")
            return self.evaluate(args[0]) - self.evaluate(args[1])
        elif operation == "*":
            if len(args) != 2:
                self.error("'*' requires 2 arguments")
            return self.evaluate(args[0]) * self.evaluate(args[1])
        elif operation == "/":
            if len(args) != 2:
                self.error("'/' requires 2 arguments")
            divisor = self.evaluate(args[1])
            if divisor == 0:
                self.error("Division by zero")
            return self.evaluate(args[0]) / self.evaluate(args[1])
        elif operation == "len":
            if len(args) != 1:
                self.error("'len' requires 1 argument")
            value = self.evaluate(args[0])
            if isinstance(value, list):
                return len(value)
            elif isinstance(value, str):
                return len(value)
            else:
                self.error("'len' can only be applied to arrays and strings")
        else:
            self.error(f"Unknown operation: {operation}")
    
    def evaluate(self, value: Any) -> Any:
        if isinstance(value, dict) and 'type' in value:
            if value['type'] == 'constant_ref':
                if value['name'] not in self.constants:
                    self.error(f"Undefined constant: {value['name']}")
                return self.evaluate(self.constants[value['name']])
            elif value['type'] == 'expression':
                return value['value']
        return value
    
    def parse_value(self):
        self.skip_whitespace()
        
        current_char = self.peek()
        
        if current_char == '-' or current_char.isdigit() or current_char == '.':
            return self.parse_number()
        elif current_char == "'":
            return self.parse_string()
        elif current_char == '(':
            return self.parse_array()
        elif current_char == '$':
            return {'type': 'expression', 'value': self.parse_constant_expression()}
        elif re.match(r'[_a-zA-Z]', current_char):
            name = self.parse_name()
            return {'type': 'constant_ref', 'name': name}
        else:
            self.error(f"Unexpected character: {current_char}")
    
    def parse_assignment(self):
        name = self.parse_name()
        self.skip_whitespace()
        
        if self.peek() != '=':
            self.error("Expected '='")
        self.advance()
        self.skip_whitespace()
        
        value = self.parse_value()
        self.skip_whitespace()
        
        if self.peek() != ';':
            self.error("Expected ';'")
        self.advance()
        
        evaluated_value = self.evaluate(value)
        self.constants[name] = evaluated_value
        
        return {'type': 'assignment', 'name': name, 'value': evaluated_value}
    
    def parse(self, text: str):
        self.pos = 0
        self.text = text
        self.line_num = 1
        self.char_pos = 1
        self.constants = {}
        
        result = []
        
        while self.pos < len(self.text):
            self.skip_whitespace()
            
            if self.pos >= len(self.text):
                break
            
            if re.match(r'[_a-zA-Z]', self.peek()):
                if self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "//":
                    continue
                if self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] == "{-":
                    continue
                    
                result.append(self.parse_assignment())
            else:
                self.error(f"Unexpected character: {self.peek()}")
        
        return result


def to_xml(data, indent=0):
    spaces = "  " * indent
    result = []
    
    if isinstance(data, list):
        result.append(f"{spaces}<array>")
        for item in data:
            result.append(to_xml(item, indent + 1))
        result.append(f"{spaces}</array>")
    elif isinstance(data, dict):
        if data['type'] == 'assignment':
            value_xml = to_xml(data['value'], indent + 1)
            result.append(f"{spaces}<assignment name=\"{data['name']}\">")
            result.append(value_xml)
            result.append(f"{spaces}</assignment>")
        else:
            result.append(f"{spaces}<value>{str(data)}</value>")
    else:
        if isinstance(data, str):
            escaped = data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            result.append(f"{spaces}<string>{escaped}</string>")
        elif isinstance(data, (int, float)):
            result.append(f"{spaces}<number>{data}</number>")
        else:
            result.append(f"{spaces}<value>{str(data)}</value>")
    
    return "\n".join(result)


def main():
    parser = argparse.ArgumentParser(description='Configuration language to XML converter')
    parser.add_argument('-i', '--input', required=True, help='Input file')
    parser.add_argument('-o', '--output', required=True, help='Output XML file')
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        config_parser = ConfigParser()
        parsed_data = config_parser.parse(content)
        
        xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_output += '<configuration>\n'
        xml_output += to_xml(parsed_data, 1)
        xml_output += '\n</configuration>'
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(xml_output)
        
        print(f"Conversion complete. Result saved to {args.output}")
        
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
