import c4d,os,types,urllib2,shutil
import xml.dom.minidom
from xml.dom.minidom import parse

class updater():
    def __init__(self):
        self.dir                   =   os.path.split(__file__)[0]

        self.server_URL_FOLDER     =   "http://gr4ph0s.free.fr/plugin/PivotMaster/"
        self.server_XML            =   self._setServer_XML()
        self.local_XML             =   xmlParser(os.path.join(self.dir, "version.xml"))
        self.fileToDownload        =   []


    def _setServer_XML(self):
        """
            Télécharge le XML du serveur
            Set server_XML en tant qu'instance de xmlParser

            :return: une instance du xmlParser ou un boolean if fail
            :rtype: bool or xmlParser()
        """
        serverUrl = self.server_URL_FOLDER+"/version.xml"
        localPath = os.path.join(self.dir,"version_from_server.xml")
        if self.downloadFile(serverUrl,localPath) == False:
            return False
        else:
            return xmlParser(os.path.join(self.dir, "version_from_server.xml"))


    def printError(self,error):
        """
            Affiche une erreur

            :param error: L'erreur à afficher
            :type error: string
        """
        c4d.gui.MessageDialog(error)

    def downloadFile(self,serverURL,localPath):
        """
            Télécharge un fichier

            :param serverURL: L'url du fichier à télécharger
            :type serverURL: string

            :param localPath: le chemin local où le fichier sera téléchargé
            :type localPath: string

            :return: True si succes, False si echec
            :rtype: bool
        """
        req = urllib2.Request(serverURL)
        try:
             u = urllib2.urlopen(serverURL)
        #On gère les erreurs
        except IOError, e:
            if hasattr(e, 'reason'):
                error = 'Nous avons échoué à joindre le serveur.\nRaison: ', e.reason
                self.printError(error)
                return False
            elif hasattr(e, 'code'):
                error = "Le serveur n'a pu satisfaire la demande.\nCode d erreur : ", e.code
                self.printError(error)
                return False
        #Si y'a pas d'erreur
        else:
            f = open(localPath, 'wb')
            meta = u.info()
            file_size = int(meta.getheaders("Content-Length")[0])
            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                #Si il n'y plus de buffer on sort de la boucle
                if not buffer:
                    break
                file_size_dl += len(buffer)
                #on écrit notre buffer dans notre fichier
                f.write(buffer)
                print serverURL.split('/')[-1]," - ",file_size_dl ," - ", file_size
            f.close()
            return True

    def needUpdate(self):
        """
            Check si une update est necessaire
            fileToDownload contiendra les fichiers à télécharger

            :return: True si besoin d'une update, False si pas besoin d'update
            :rtype: bool
        """
        #On check si self.server_XML n'est pas False c'est qu'il s'agit d'une instance xmlParser
        if self.server_XML != False:
            #On check si la version global du serveur est supérieur à celle en local
            if self.server_XML.getRevision() > self.local_XML.getRevision():
                #On recup les fichiers des XML
                local = self.local_XML.getFile()
                server = self.server_XML.getFile()
                #On défini les fichiers a téléchargé
                self.fileToDownload = self.getFileToDownload(local,server)
                #Si il n'y a rien à telechargé
                if len(self.fileToDownload) != 0:
                    return True
                else :
                    return False
            else :
                return False
        else:
            return False

    def doUpdate(self):
        """
            Télécharge les différents fichiers nécessaire pour faire la MAJ

            :return: True si tout les fichiers on étais mis à jour, False si il y à eu une erreur lors d'un téléchargement'
            :rtype: bool
        """
        #On parcour chaque fichier
        for files in self.fileToDownload:
            if files[1] == "None":
                files[1] = ""
            pathLocal  = os.path.join(self.dir,files[1],files[2])
            pathServer = self.server_URL_FOLDER + files[1] + files[2]
            #On télécharge le fichier et si y'a une erreur on arrête tout
            if self.downloadFile(pathServer,pathLocal) == False:
                break
                return False
        return True

    def cleanFile(self):
        """
            Met à jour version.xml en local et supprime le xml du serveur

            :return: True si tout le xml à étais mis à jour, False si il y à eu une erreur
            :rtype: bool
        """
        pathLocalXML = os.path.join(self.dir, "version.xml")
        pathServerXML = os.path.join(self.dir, "version_from_server.xml")
        if os.path.isfile(pathLocalXML) == True and os.path.isfile(pathServerlXML) == True:
            shutil.copy(pathServerXML,pathLocalXML)
            os.remove(pathServerXML)
            return True
        else :
            return False


    def getFileToDownload(self,localFile,serverFile):
        """
            Récupère la liste des fichiers à mettre à jour.

            :param localFile: Une liste contenant la lsite des fichiers local
            :type localFile: Liste

            :param serverFile: Une liste contenant la lsite des fichiers sur le serveur
            :type serverFile: Liste

            :return: Une lsite contenant les fichiers à mettre à jour
            :rtype: liste
        """
        isInTheFile = False
        filecounter = 0
        abuffer = []

        #On parcour notre liste de fichier du serveur
        for server in serverFile:
            isInTheFile = False
            filecounter = 0

            #Pour chaque fichier du serveur on parcours chaque fichier local
            for local in localFile:
                filecounter += 1
                #Si les noms sont identiques
                if server[0] == local[0]:
                    isInTheFile = True
                    #Si la version du serveur est plus grande que la local
                    if server[3] > local[3]:
                        abuffer.append(server)
                #Si les fichier n'est pas dans le xml et qu'on a tout parcouru
                if isInTheFile == False and filecounter == len(localFile):
                    abuffer.append(server)
        return abuffer


class xmlParser():
    def __init__(self,fileName):
        self.xmlFile         =    fileName
        self.xmlStream       =    xml.dom.minidom.parse(fileName)
        self.collection      =    self.xmlStream.documentElement
        self.dataList        =    None

    def getRevision(self):
        """
            Récupère la révision d'un fichier

            :return: Une valeur correspondant à la version de la révision
            :rtype: int
        """
        self.dataList = self.collection.getElementsByTagName("revision")
        for data in self.dataList:
            return int(data.getElementsByTagName('version')[0].childNodes[0].data)

    def getFile(self):
        """
            Récupère la liste des fichiers d'un XML ainsi que leur data'

            :return: Une liste de liste des fichiers et de leurs options.
            :rtype: Liste
        """
        abuffer = []
        self.dataList = self.collection.getElementsByTagName("file")
        for data in self.dataList:
            title    = str(data.getAttribute("title"))
            path     = str(data.getElementsByTagName('dir')[0].childNodes[0].data)
            fileName = str(data.getElementsByTagName('fileName')[0].childNodes[0].data)
            version  = int(data.getElementsByTagName('version')[0].childNodes[0].data)

            abuffer.append([title,
                            path,
                            fileName,
                            version
                            ])
        return abuffer

def main() :


    update = updater()
    if update.needUpdate() == True:
        print 'je fait une update'
        update.doUpdate()
        update.cleanFile() #On clean les fichiers tempo
    else:
        update.cleanFile() #On clean les fichiers tempo
        print "Pas besoin d'update"


if __name__=='__main__':
    main()

