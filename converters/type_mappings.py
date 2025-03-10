SWIFT_TO_KOTLIN_TYPE_MAPPINGS = {
    'String': 'String',
    'Int': 'Int',
    'Double': 'Double',
    'Float': 'Float',
    'Bool': 'Boolean',
    '[String]': 'List<String>',
    '[Int]': 'List<Int>',
    'Date': 'LocalDateTime',
    'UUID': 'String',
    'Data': 'ByteArray',
    'Optional<String>': 'String?',
    'Optional<Int>': 'Int?',
    'Optional<Bool>': 'Boolean?',
    'Any': 'Any',
    'AnyObject': 'Any',
    'Void': 'Unit'
}

DEFAULT_IMPORTS = """
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import java.time.LocalDateTime
""".strip()