import unittest
from dz import ConfigParser, to_xml


class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()
    
    def test_numbers(self):
        # Целые числа
        result = self.parser.parse("x = 42;")
        self.assertEqual(result[0]['value'], 42)
        
        # Отрицательные числа
        result = self.parser.parse("x = -42;")
        self.assertEqual(result[0]['value'], -42)
        
        # Дробные числа
        result = self.parser.parse("x = 3.14;")
        self.assertAlmostEqual(result[0]['value'], 3.14)
        
        # Числа в экспоненциальной форме
        result = self.parser.parse("x = 1.5e2;")
        self.assertAlmostEqual(result[0]['value'], 150.0)
    
    def test_strings(self):
        result = self.parser.parse("msg = 'Hello World';")
        self.assertEqual(result[0]['value'], 'Hello World')
        
        # Строка с экранированием
        result = self.parser.parse("msg = 'It\\'s great';")
        self.assertEqual(result[0]['value'], "It's great")
    
    def test_arrays(self):
        result = self.parser.parse("arr = (1, 2, 3);")
        self.assertEqual(result[0]['value'], [1, 2, 3])
        
        result = self.parser.parse("arr = ('a', 'b', 'c');")
        self.assertEqual(result[0]['value'], ['a', 'b', 'c'])
        
        result = self.parser.parse("arr = (1, 'text', 3.14);")
        self.assertEqual(result[0]['value'], [1, 'text', 3.14])
    
    def test_constants(self):
        result = self.parser.parse("""
            x = 10;
            y = x;
        """)
        self.assertEqual(self.parser.constants['x'], 10)
        self.assertEqual(self.parser.constants['y'], 10)
    
    def test_constant_expressions(self):
        # Сложение
        result = self.parser.parse("x = $[+ 10 20];")  # Было: %[+ 10 20]
        self.assertEqual(result[0]['value'], 30)
        
        # Вычитание
        result = self.parser.parse("x = $[- 50 20];")  # Было: %[- 50 20]
        self.assertEqual(result[0]['value'], 30)
        
        # Умножение
        result = self.parser.parse("x = $[* 5 6];")  # Было: %[* 5 6]
        self.assertEqual(result[0]['value'], 30)
        
        # Деление
        result = self.parser.parse("x = $[/ 60 2];")  # Было: %[/ 60 2]
        self.assertEqual(result[0]['value'], 30)
        
        # len для строк
        result = self.parser.parse("x = $[len 'hello'];")  # Было: %[len 'hello']
        self.assertEqual(result[0]['value'], 5)
        
        # len для массивов
        result = self.parser.parse("x = $[len (1, 2, 3, 4, 5)];")  # Было: %[len (1, 2, 3, 4, 5)]
        self.assertEqual(result[0]['value'], 5)
    
    def test_complex_expressions(self):
        result = self.parser.parse("""
            a = 10;
            b = 20;
            c = $[+ a b];  # Было: %[+ a b]
            d = $[* c 2];  # Было: %[* c 2]
        """)
        self.assertEqual(self.parser.constants['c'], 30)
        self.assertEqual(self.parser.constants['d'], 60)
    
    def test_comments(self):
        # Однострочные комментарии
        result = self.parser.parse("""
            // Это комментарий
            x = 42; // И это комментарий
            y = 100;
        """)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['value'], 42)
        self.assertEqual(result[1]['value'], 100)
        
        # Многострочные комментарии
        result = self.parser.parse("""
            {-
            Это
            многострочный
            комментарий
            -}
            x = 42;
        """)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], 42)
    
    def test_to_xml(self):
        data = [{'type': 'assignment', 'name': 'test', 'value': 42}]
        xml = to_xml(data)
        self.assertIn('<assignment name="test">', xml)
        self.assertIn('<number>42</number>', xml)


if __name__ == '__main__':
    unittest.main()
